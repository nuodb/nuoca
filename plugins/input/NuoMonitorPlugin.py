# (C) Copyright NuoDB, Inc. 2017-2020
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.

import logging
import os
import re
import socket
import threading
import time

from copy import deepcopy
from pynuoca.nuoca_plugin import NuocaMPInputPlugin
from pynuoca.nuoca_util import nuoca_log
from pynuoca.nuomon.nuomon_monitor import DomainListener, MetricsDomain
from pynuoca.nuomon.nuomon_broadcast import MetricsConsumer, MetricsProducer, \
    MetricsListener, EventListener


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
        nuoca_log(logging.DEBUG, "NuoMon: NuoMonHandler.__init__()")
        self.nuo_monitor_obj = nuo_monitor_obj
        pass

    def onMetrics(self, description):
        nuoca_log(logging.DEBUG, "NuoMon: NuoMonHandler.onMetrics()")
        pass

    def onValues(self, values):
        nuoca_log(logging.DEBUG, "NuoMon: NuoMonHandler.onValues()")
        self.nuo_monitor_obj.nuomonitor_collect_queue.append(deepcopy(values))
        pass


class NuoMonitorPlugin(NuocaMPInputPlugin):
    def __init__(self, parent_pipe):
        super(NuoMonitorPlugin, self).__init__(parent_pipe, 'NuoMon')
        self._config = None
        self._broker = None
        self._enabled = False
        self._numon_handler_ready = False
        self._domain = None
        self._domain_username = 'domain'
        self._domain_password = 'bird'
        self._domain_metrics = None
        self._domain_metrics_host = None
        self._database_regex_pattern = '.*'
        self._host_uuid_shortname = False
        self._thread = None
        self._nuomonitor_collect_queue = []
        self._collection_interval = 30

    def wait_for_terminate(self):
        if self._domain:
            self._domain.waitForTerminate()

    def get_nuodb_metrics(self, broker, password, listener, user='domain',
                          database=None, host=None, process=None, args=None,
                          domain_listener=None):
        # Listener is class derived from MetricsListener
        if listener is None:
            listener = MetricsListener
        if domain_listener is None:
            domain_listener = EventListener

        self._domain = DomainListener(user=user,
                                      password=password,
                                      database=database,
                                      host=host,
                                      process=process,
                                      listener=listener,
                                      args=args,
                                      domain_listener=domain_listener())
        return MetricsDomain(broker, user, password, self._domain)

    @property
    def nuomonitor_collect_queue(self):
        return self._nuomonitor_collect_queue

    def _nuomon_handler_thread(self):
        obj = NuoMonHandler(self)
        obj.start()
        self._numon_handler_ready = True
        time.sleep(10)
        self.wait_for_terminate()
        nuoca_log(logging.INFO, "NuoMon: NuoDB connection terminated")
        self._domain_metrics.disconnect()
        self._numon_handler_ready = False
        while not self._numon_handler_ready:
            time.sleep(self._collection_interval)
            nuoca_log(logging.INFO, "NuoMon: calling startup")
            self.startup_nuomon()

    def startup_nuomon(self):
        try:
            self._numon_handler_ready = False
            self._domain_metrics = \
                self.get_nuodb_metrics(
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
            nuoca_log(logging.ERROR, "NuoMon Startup error: %s" % str(e))
            return False

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
            nuoca_log(logging.INFO, "NuoMon: plugin config: %s" %
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
            self.startup_nuomon()
            return self._numon_handler_ready
        except Exception as e:
            nuoca_log(logging.ERROR, "NuoMon Plugin Startup error: %s" % str(e))
            return False

    def shutdown(self):
        self._enabled = False
        pass

    def collect(self, collection_interval):
        uuid_hostname_regex = \
            '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}-'
        rval = None
        self._collection_interval = collection_interval
        try:
            nuoca_log(logging.DEBUG, "NuoMon: collect()")
            base_values = super(NuoMonitorPlugin, self).collect(collection_interval)
            collection_count = len(self._nuomonitor_collect_queue)
            nuoca_log(logging.DEBUG, "NuoMon: collection_count %s" %
                      str(collection_count))
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
