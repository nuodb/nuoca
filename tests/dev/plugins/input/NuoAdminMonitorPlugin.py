import logging
import os
import re
import requests
import threading
import time

from nuoca_plugin import NuocaMPInputPlugin
from nuoca_util import nuoca_log
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
    self._thread = None
    self._admin_collect_interval = 10
    self._monitor_collect_queue = []

  @property
  def monitor_collect_queue(self):
    return self._monitor_collect_queue

  def get_enforcer(self):
    req = requests.get(self._domain_enforcer_url)
    if req.status_code != 200:
      nuoca_log(logging.ERROR,
                "Error code '%d' when calling Admin Rest API: %s" % (req.status_code, self._domain_enforcer_url))
      return None
    return req.json()

  def _nuomon_handler_thread(self):
    # obj = NuoMonHandler(self)
    # obj.start()
    self._numon_handler_ready = True
    self._domain_metrics.wait_forever()

  def startup(self, config=None):
    try:
      self._config = config

      # Validate the configuration.
      required_config_items = ['admin_host', 'domain_username', 'domain_password']
      if not self.has_required_config_items(config, required_config_items):
        return False
      nuoca_log(logging.INFO, "NuoAdminMonitor plugin config: %s" %
                str(self._config))

      self._admin_host = os.path.expandvars(config['admin_host'])
      self._domain_username = os.path.expandvars(config['domain_username'])
      self._domain_password = os.path.expandvars(config['domain_password'])
      self._base_url = "http://%s:%s/api/2" % (self._admin_host,
                                               self._admin_rest_api_port)
      self._domain_enforcer_url = "%s/domain/enforcer" % self._base_url
      self._regions_url = "%s/regions" % self._base_url
      self._auth = HTTPBasicAuth(self._domain_username,
                                 self._domain_password)
      if 'database_regex_pattern' in config:
        self._database_regex_pattern = config['database_regex_pattern']
      if 'host_uuid_shortname' in config:
        self._host_uuid_shortname = config['host_uuid_shortname']
      r = requests.get()
      self._enabled = True
      # self._domain_metrics = \
      #   get_nuodb_metrics(
      #     self._admin_host,
      #     self._domain_password,
      #     listener=MetricsProducer,
      #     user=self._domain_username)
      # self._thread = threading.Thread(target=self._nuomon_handler_thread)
      self._thread.daemon = True
      self._thread.start()
      try_count = 0
      while not self._numon_handler_ready and try_count < 5:
        try_count += 1
        time.sleep(1)
      return self._numon_handler_ready
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
        m = re.search(self._database_regex_pattern, collected_dict['Database'])
        if m:
          if self._host_uuid_shortname:
            m2 = re.search(uuid_hostname_regex, collected_dict['Hostname'])
            if m2:
              shortid = collected_dict['Hostname'][37:]
              if 'NodeType' in collected_dict:
                if collected_dict['NodeType'] == 'Transaction':
                  shortid += "(TE)"
                elif collected_dict['NodeType'] == 'Storage':
                  shortid += "(SM)"
              shortid_with_pid = shortid + str(collected_dict['ProcessId'])
              collected_dict['HostShortID'] = shortid
              collected_dict['HostShortIDwithPID'] = shortid_with_pid
          rval.append(collected_dict)
    except Exception as e:
      nuoca_log(logging.ERROR, str(e))
    return rval
