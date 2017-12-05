# Copyright (c) 2017, NuoDB, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of NuoDB, Inc. nor the names of its contributors may
#       be used to endorse or promote products derived from this software
#       without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL NUODB, INC. BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA,
# OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
# ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import logging
import os
import re
import socket
import threading
import time

from copy import deepcopy
from nuoca_plugin import NuocaMPInputPlugin
from nuoca_util import nuoca_log
from nuomon.nuomon_monitor import get_nuodb_metrics
from nuomon.nuomon_broadcast import MetricsConsumer, MetricsProducer

# NuoMonitor plugin
#
# Example NuoMonitor plugin configuration:
#
# - NuoMonitor:
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
    self.nuo_monitor_obj.nuomonitor_collect_queue.append(deepcopy(values))
    pass


class NuoMonitorPlugin(NuocaMPInputPlugin):
  def __init__(self, parent_pipe):
    super(NuoMonitorPlugin, self).__init__(parent_pipe, 'NuoMon')
    self._config = None
    self._broker = None
    self._enabled = False
    self._numon_handler_ready = False
    self._domain_username = 'domain'
    self._domain_password = 'bird'
    self._domain_metrics = None
    self._domain_metrics_host = None
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

      # Don't reveal the domain password in the NuoCA log file.
      display_config = {}
      display_config.update(config)
      display_config['domain_password'] = ''
      nuoca_log(logging.INFO, "NuoAdminMonitor plugin config: %s" %
                str(display_config))

      self._broker = os.path.expandvars(config['broker'])
      self._domain_username = os.path.expandvars(config['domain_username'])
      self._domain_password = os.path.expandvars(config['domain_password'])
      if 'domain_metrics_host' in config:
        self._domain_metrics_host = os.path.expandvars(config['domain_metrics_host'])
        if self._domain_metrics_host == 'localhost':
          self._domain_metrics_host = socket.gethostname()
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
          user=self._domain_username,
          host=self._domain_metrics_host)
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
      base_values = super(NuoMonitorPlugin, self).collect(collection_interval)
      collection_count = len(self._nuomonitor_collect_queue)
      if not collection_count:
        return rval

      rval = []
      for i in range(collection_count):
        collected_dict = self._nuomonitor_collect_queue.pop(0)
        if self._domain_metrics_host:
          if collected_dict['Hostname'] != self._domain_metrics_host:
            continue
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
