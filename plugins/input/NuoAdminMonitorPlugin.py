import logging
import os
import requests
import threading

from nuoca_plugin import NuocaMPInputPlugin
from nuoca_util import nuoca_log, nuoca_gettimestamp, IntervalSync
from requests.auth import HTTPBasicAuth

# NuoAdminMonitor plugin
#
# Example NuoAdminMonitor plugin configuration:
#
# - NuoAdminMonitor:
#    description : Monitor NuoDB Admin layer
#    admin_host: localhost
#    admin_rest_api_port: 8888
#    domain_username: domain
#    domain_password: bird
#    admin_collect_interval: 10
#    admin_collect_timeout: 1

class NuoAdminMonitorPlugin(NuocaMPInputPlugin):
  def __init__(self, parent_pipe):
    super(NuoAdminMonitorPlugin, self).__init__(parent_pipe, 'NuoAdminMon')
    self._config = None
    self._admin_host = None
    self._admin_rest_api_port = 8888
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
    self._host_uuid_shortname = False
    self._timer_thrd = None
    self._admin_collect_interval = 10
    self._admin_collect_timeout = 1
    self._admin_collect_sync = None
    self._monitor_collect_queue = []

  @property
  def monitor_collect_queue(self):
    return self._monitor_collect_queue

  def get_rest_url(self, rest_url):
    try:
      req = requests.get(rest_url, auth=self._auth,
                         timeout=self._admin_collect_timeout)
      if req.status_code != 200:
        err_msg = "NuoAdminMon: Error code '%d' when " \
                  "calling Admin Rest API: %s" \
                  % (req.status_code, rest_url)
        nuoca_log(logging.ERROR, err_msg)
        return {'nuoca_collection_error': err_msg}
      return req.json()
    except requests.RequestException as e:
      err_msg = str(e)
      nuoca_log(logging.ERROR, err_msg)
      return {'nuoca_collection_error': err_msg}
    except Exception as e:
      err_msg = str(e)
      nuoca_log(logging.ERROR, err_msg)
      return {'nuoca_collection_error': err_msg}

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
    database_boolean_fields = \
    [u'active', u'ismet']

    collect_timestamp = nuoca_gettimestamp() * 1000

    #print "\n\nCollection Timestamp: %s" % collect_timestamp
    enforcer_result = self.get_enforcer()
    #print "Result from Rest API %s: %s" % (self._domain_enforcer_url, enforcer_result)
    if 'nuoca_collection_error' in enforcer_result:
      results = {"TimeStamp": collect_timestamp}
      results['nuoca_collection_error'] = \
        enforcer_result['nuoca_collection_error']
      self._monitor_collect_queue.append(results)
    regions_result = self.get_regions()
    #print "Result from Rest API %s: %s" % (self._regions_url, regions_result)
    if 'nuoca_collection_error' in regions_result:
      results = {"TimeStamp": collect_timestamp}
      results['nuoca_collection_error'] = \
        regions_result['nuoca_collection_error']
      self._monitor_collect_queue.append(results)
    else:
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
            if database_field in database_boolean_fields:
              database_results["database.%s" % database_field] = \
                str(database[database_field]).lower()
            else:
              database_results["database.%s" % database_field] = \
                str(database[database_field])
          database_results.update(results)
          self._monitor_collect_queue.append(database_results)
        region_count += 1

  def _timer_thread(self):
    while(self._enabled):
      collect_timestamp = self._admin_collect_sync.wait_for_next_interval()
      collect_thread = threading.Thread(target=self._collector_thread,
                                        args=(collect_timestamp,))
      collect_thread.daemon = True
      collect_thread.start()

  def startup(self, config=None):
    try:
      self._config = config

      # Validate the configuration.
      required_config_items = ['admin_host', 'domain_username',
                               'domain_password']
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
      if 'admin_collect_interval' in config:
        self._admin_collect_interval = config['admin_collect_interval']
      if 'admin_collect_timeout' in config:
        self._admin_collect_interval = config['admin_collect_timeout']
      if 'host_uuid_shortname' in config:
        self._host_uuid_shortname = config['host_uuid_shortname']
      if 'admin_rest_api_port' in config:
        if isinstance(config['admin_rest_api_port'], int):
          self._admin_rest_api_port = config['admin_rest_api_port']
        else:
          self._admin_rest_api_port = int(os.path.expandvars(
              config['admin_rest_api_port']))
      self._base_url = "http://%s:%d/api/2" % (self._admin_host,
                                               self._admin_rest_api_port)
      self._domain_enforcer_url = "%s/domain/enforcer" % self._base_url
      self._regions_url = "%s/regions" % self._base_url
      self._auth = HTTPBasicAuth(self._domain_username,
                                 self._domain_password)
      nuoca_start_ts = None
      if 'nuoca_start_ts' in config:
        nuoca_start_ts = config['nuoca_start_ts']
      self._admin_collect_sync = IntervalSync(self._admin_collect_interval,
                                              seed_ts=nuoca_start_ts)

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
    rval = None
    try:
      nuoca_log(logging.DEBUG, "Called collect() in NuoAdminMonitor Plugin process")
      base_values = super(NuoAdminMonitorPlugin, self).collect(collection_interval)
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
