import logging
import os
import re
import threading
import time

from nuoca_plugin import NuocaMPInputPlugin
from nuoca_util import nuoca_log
from nuomon.nuomon_monitor import get_nuodb_metrics
from nuomon.nuomon_broadcast import MetricsConsumer, MetricsProducer

# mpNuoMonitor plugin
#
# Example mpNuoMonitor plugin configuration:
#
# - mpNuoMonitor:
#    description : Collection from internal nuomonitor tool
#    database_regex_pattern: dbt2
#    broker: 172.19.0.16
#    domain_username: domain
#    domain_password: bird


class NuoMonHandler(MetricsConsumer):
  """ NuoMon handler that listens for messages from BroadcastListener."""

  nuo_monitor_obj = None

  def __init__(self, nuo_monitor_obj):
    super(NuoMonHandler, self).__init__()
    self.nuo_monitor_obj = nuo_monitor_obj
    pass

  def onMetrics(self, description):
    pass

  def onValues(self, values):
    self.nuo_monitor_obj.nuomonitor_collect_queue.append(values)
    pass


class MPNuoMonitor(NuocaMPInputPlugin):
  def __init__(self, parent_pipe):
    super(MPNuoMonitor, self).__init__(parent_pipe, 'NuoMon')
    self._config = None
    self._broker = None
    self._enabled = False
    self._numon_handler_ready = False
    self._domain_username = 'domain'
    self._domain_password = 'bird'
    self._domain_metrics = None
    self._database_regex_pattern = '.*'
    self._host_uuid_shortname = False
    self._thread = None
    self._nuomonitor_collect_queue = []

  @property
  def nuomonitor_collect_queue(self):
    return self._nuomonitor_collect_queue

  def _nuomon_handler_thread(self):
    obj = NuoMonHandler(self)
    obj.start()
    self._numon_handler_ready = True
    self._domain_metrics.wait_forever()

  def startup(self, config=None):
    try:
      self._config = config

      # Validate the configuration.
      required_config_items = ['broker', 'domain_username', 'domain_password']
      if not self.has_required_config_items(config, required_config_items):
        return False
      nuoca_log(logging.INFO, "NuoMonitor plugin config: %s" %
                str(self._config))

      self._broker = os.path.expandvars(config['broker'])
      self._domain_username = os.path.expandvars(config['domain_username'])
      self._domain_password = os.path.expandvars(config['domain_password'])
      if 'database_regex_pattern' in config:
        self._database_regex_pattern = config['database_regex_pattern']
      if 'host_uuid_shortname' in config:
        self._host_uuid_shortname = config['host_uuid_shortname']
      self._enabled = True
      self._domain_metrics = \
        get_nuodb_metrics(
          self._broker,
          self._domain_password,
          listener=MetricsProducer,
          user=self._domain_username)
      self._thread = threading.Thread(target=self._nuomon_handler_thread)
      self._thread.daemon = True
      self._thread.start()
      try_count = 0
      while not self._numon_handler_ready and try_count < 5:
        try_count += 1
        time.sleep(1)
      return self._numon_handler_ready
    except Exception as e:
      nuoca_log(logging.ERROR, "NuoMon Plugin: %s" % str(e))
      return False

  def shutdown(self):
    self.enabled = False
    pass

  def collect(self, collection_interval):
    uuid_hostname_regex = \
      '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}-'
    rval = None
    try:
      nuoca_log(logging.DEBUG, "Called collect() in NuoMonitor Plugin process")
      base_values = super(MPNuoMonitor, self).collect(collection_interval)
      collection_count = len(self._nuomonitor_collect_queue)
      if not collection_count:
        return rval

      rval = []
      for i in range(collection_count):
        collected_dict = self._nuomonitor_collect_queue.pop(0)
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
