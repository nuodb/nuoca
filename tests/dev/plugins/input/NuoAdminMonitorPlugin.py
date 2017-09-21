import logging
import os
import re
import requests
import threading
import time

from nuoca_plugin import NuocaMPInputPlugin
from nuoca_util import nuoca_log, nuoca_gettimestamp
from requests.auth import HTTPBasicAuth

# NuoAdminMonitor plugin
#
# Example NuoAdminMonitor plugin configuration:
#
# - NuoAdminMonitor:
#    description : Monitor NuoDB Admin layer
#    admin_host: 172.19.0.16
#    admin_rest_api_port: 8888
#    domain_username: domain
#    domain_password: bird
#    admin_collect_interval: 10
#    admin_collect_timeout: 1

class NuoAdminMonitor(NuocaMPInputPlugin):
  def __init__(self, parent_pipe):
    super(NuoAdminMonitor, self).__init__(parent_pipe, 'NuoAdminMon')
    self._config = None
    self._admin_host = None
    self._admin_rest_api_port = '8888'
    self._enabled = False
    self._auth = None
    self._base_url = None
    #
    # API endpoints:
    self._domain_enforcer_url = None
    #
    # self._numon_handler_ready = False
    self._domain_username = 'domain'
    self._domain_password = 'bird'
    self._domain_metrics = None
    self._database_regex_pattern = '.*'
    self._host_uuid_shortname = False
    self._timer_thrd = None
    self._admin_collect_interval = 10
    self._admin_collect_timeout = 1
    self._monitor_collect_queue = []

  @property
  def monitor_collect_queue(self):
    return self._monitor_collect_queue

  def get_rest_url(self, rest_url):
    try:
      req = requests.get(rest_url, auth=self._auth,
                         timeout=self._admin_collect_timeout)
      if req.status_code != 200:
        err_msg = "Error code '%d' when calling Admin Rest API: %s" \
                  % (req.status_code, self.rest_url)
        nuoca_log(logging.ERROR, err_msg)
        return {'nuoca_collection_error', err_msg}
      return req.json()
    except requests.RequestException as e:
      return {'nuoca_collection_error', str(e)}
    except Exception as e:
      return {'nuoca_collection_error', str(e)}

  def get_enforcer(self):
    return self.get_rest_url(self._domain_enforcer_url)

  def get_regions(self):
    return self.get_rest_url(self._regions_url)

  def _collector_thread(self, collect_timestamp):
    region_result_desired_fields = [u'region']
    host_result_desired_fields = \
      [u'stableId', u'hostname', u'port', u'version', u'address',
       u'isBroker',u'ipaddress', u'id']
    host_tags_desired_fields = \
      [u'default_archive_base', u'journal_base', u'archive_base',
       u'default_region', u'region', u'os_num_cpu', u'cores', u'os_num_cores',
       u'default_journal_base', u'ostype', u'cputype', u'os_ram_mb',
       u'osversion', u'os_num_fs']
    processes_desired_fields = \
      [u'status', u'uid', u'hostname', u'pid', u'nodeId', u'port',
       u'version', u'address', u'agentid', u'type', u'dbname']
    databases_desired_fields = \
    [u'status', u'name', u'tagConstraints', u'variables', u'groupOptions',
     u'archivesByGroup', u'archives', u'template', u'active',
     u'unmet_messages', u'options', u'ismet']

    enforcer_result = self.get_enforcer()
    regions_result = self.get_regions()
    print regions_result
    region_count = 0
    for region in regions_result:
      results = {"TimeStamp": collect_timestamp}
      results[u'domainEnforcerEnabled'] = \
        enforcer_result[u'domainEnforcerEnabled']
      for region_field in region_result_desired_fields:
        results[region_field] = regions_result[region_count][region_field]
      for host in region['hosts']:
        for host_field in host_result_desired_fields:
          results["admin.%s" % host_field] = host[host_field]
        for host_tag_field in host_tags_desired_fields:
          results["tag.%s" % host_tag_field] = host['tags'][host_tag_field]
        for process in host['processes']:
          process_results = {}
          for process_field in processes_desired_fields:
            process_results["process.%s" % process_field] \
              = process[process_field]
          process_results.update(results)
          self._monitor_collect_queue.append(process_results)
      for database in region['databases']:
        database_results = {}
        for database_field in databases_desired_fields:
          database_results["database.%s" % database_field] = \
            str(database[database_field])
        database_results.update(results)
        self._monitor_collect_queue.append(database_results)
      region_count += 1

  def _timer_thread(self):
    while(self._enabled):
      collect_timestamp = nuoca_gettimestamp()
      collect_thread = threading.Thread(target=self._collector_thread,
                                        args=(collect_timestamp,))
      collect_thread.daemon = True
      collect_thread.start()
      next_collection_timestamp = collect_timestamp + \
                                  self._admin_collect_interval
      time.sleep(next_collection_timestamp - collect_timestamp)


  def startup(self, config=None):
    try:
      self._config = config

      # Validate the configuration.
      required_config_items = ['admin_host', 'domain_username', 'domain_password']
      if not self.has_required_config_items(config, required_config_items):
        return False

      # Don't reveal the domain password in the NuoCA log file.
      display_config = {}
      display_config.update(config)
      display_config['domain_password'] = ''
      nuoca_log(logging.INFO, "NuoAdminMonitor plugin config: %s" %
                str(display_config))

      self._admin_host = os.path.expandvars(config['admin_host'])
      self._domain_username = os.path.expandvars(config['domain_username'])
      self._domain_password = os.path.expandvars(config['domain_password'])
      self._base_url = "http://%s:%s/api/2" % (self._admin_host,
                                               self._admin_rest_api_port)
      self._domain_enforcer_url = "%s/domain/enforcer" % self._base_url
      self._regions_url = "%s/regions" % self._base_url
      self._auth = HTTPBasicAuth(self._domain_username,
                                 self._domain_password)
      if 'admin_collect_interval' in config:
        self._admin_collect_interval = config['admin_collect_interval']
      if 'admin_collect_timeout' in config:
        self._admin_collect_interval = config['admin_collect_timeout']
      if 'database_regex_pattern' in config:
        self._database_regex_pattern = config['database_regex_pattern']
      if 'host_uuid_shortname' in config:
        self._host_uuid_shortname = config['host_uuid_shortname']
      self._enabled = True
      self._timer_thrd = threading.Thread(target=self._timer_thread)
      self._timer_thrd.daemon = True
      self._timer_thrd.start()
      return True
    except Exception as e:
      nuoca_log(logging.ERROR, "NuoAdminMonitor Plugin: %s" % str(e))
      return False

  def shutdown(self):
    self.enabled = False
    pass

  def collect(self, collection_interval):
    uuid_hostname_regex = \
      '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}-'
    rval = None
    try:
      nuoca_log(logging.DEBUG, "Called collect() in NuoAdminMonitor Plugin process")
      base_values = super(NuoAdminMonitor, self).collect(collection_interval)
      collection_count = len(self.monitor_collect_queue)
      if not collection_count:
        return rval

      rval = []
      for i in range(collection_count):
        collected_dict = self.monitor_collect_queue.pop(0)
        rval.append(collected_dict)
    except Exception as e:
      nuoca_log(logging.ERROR, str(e))
    return rval
