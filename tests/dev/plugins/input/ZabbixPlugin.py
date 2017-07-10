import json
import logging
import subprocess
import re
import requests
import threading
import time

from nuoca_plugin import NuocaMPInputPlugin
from nuoca_util import nuoca_log, search_running_processes

# mpZabbix plugin
#
# This plugin expects that a zabbix agent is running on the localhost
#
# Example mpZabbix plugin configuration:
#
# - mpZabbix:
#    description : Collect machine stats from Zabbix
#

class MPZabbix(NuocaMPInputPlugin):
  def __init__(self, parent_pipe):
    super(MPZabbix, self).__init__(parent_pipe, 'ZBX')
    self._config = None

  def _autoDiscoverMonitors(self):
    # TODO
    pass

  def _collection_cycle(self, next_interval_time):
    rval = None
    try:
        return rval
    except Exception as e:
      nuoca_log(logging.ERROR, "ZBX collection error: %s" % str(e))
    return rval


  def startup(self, config=None):
    try:
      self._config = config

      # Make sure that zabbix agent is running.
      zabbix_agentd = search_running_processes('zabbix_agentd')
      if not zabbix_agentd:
        nuoca_log(logging.ERROR, "Zabbix agent daemon is not running.")
        return False

      # Make sure that zabbix_get is installed.
      p = subprocess.Popen(["which", "zabbix_get"], stdout=subprocess.PIPE)
      out, err = p.communicate()
      if p.returncode != 0 or 'zabbix_get' not in out:
        nuoca_log(logging.ERROR, "Cannot locate zabbix_get command.")
        return False

      # Validate the configuration.
      if not config:
        nuoca_log(logging.ERROR, "ZBX plugin missing config")
        return False
      required_config_items = ['autoDiscoverMonitors', 'server', 'keys']
      for config_item in required_config_items:
        if config_item not in config:
          nuoca_log(logging.ERROR,
                    "ZBX plugin '%s' missing from config" %
                    config_item)
          return False

      nuoca_log(logging.INFO, "ZBX plugin config: %s" %
                str(self._config))

      return True
    except Exception as e:
      nuoca_log(logging.ERROR, str(e))
      return False

  def shutdown(self):
    pass

  def collect(self, collection_interval):
    rval = []
    collected_values = super(MPZabbix, self).collect(
      collection_interval)
    try:
      for key in self._config['keys']:
        p = subprocess.Popen(['zabbix_get', '-s', 'localhost', '-k', key], stdout=subprocess.PIPE)
        out, err = p.communicate()
        if p.returncode != 0:
          nuoca_log(logging.ERROR, "Problem with zabbix_get command.")
          return False
        collected_values[key] = out
      rval.append(collected_values)
    except Exception as e:
      nuoca_log(logging.ERROR, str(e))
    return rval
