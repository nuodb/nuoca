import logging
import re

from nuoca_plugin import NuocaMPInputPlugin
from nuoca_util import nuoca_log, search_running_processes, \
  execute_command, coerce_numeric

# mpZabbix plugin
#
# This plugin expects that a zabbix agent is running on the localhost and
# zabbix_get is installed on the localhost.  The 'ZBX' section of the NuoCA
# config is used to control this Zabbix plugin.  The system metrics collected
# by zabbix is controlled by the 'keys' section.  The key names are in the
# Zabbix key name format.  The 'autoDiscoverMonitors' boolean is used to
# automatically include file system mounts, devices, and network interfaces in
# the collected 'keys'
#
# This was developed and tested using Zabbix 2.2.11-1 on Ubuntu.
#
# Example Zabbix plugin configuration:
#
# - ZBX:
#    description : Collect machine stats from Zabbix
#    server: localhost
#    autoDiscoverMonitors: true
#    keys:
#    - system.uptime
#    - system.cpu.intr
#    - vm.memory.size[available]
#    - system.cpu.switches
#    - system.cpu.util[, interrupt]
#    - system.boottime
#    - system.cpu.util[, idle]
#    - system.cpu.util[, system]
#    - system.cpu.util[, iowait]
#    - system.cpu.util[, nice]
#    - system.cpu.util[, user]
#    - system.cpu.util[, softirq]
#    - system.localtime
#    - system.cpu.util[, steal]
#    - system.users.num
#    - proc.num[]
#    - vm.memory.size[total]
#    - system.uname
#    - system.hostname
#    - kernel.maxproc
#    - kernel.maxfiles
#

class MPZabbix(NuocaMPInputPlugin):
  def __init__(self, parent_pipe):
    super(MPZabbix, self).__init__(parent_pipe, 'ZBX')
    self._config = None

  def _append_config_key(self, key):
    nuoca_log(logging.INFO, "ZBX plugin appending config key: %s" % key)
    self._config['keys'].append(key)

  def _auto_discover_monitors(self):
    devices = []
    mounts = []
    interfaces = []

    # discover file system mounts & devices
    for line in execute_command("mount")[1].split("\n"):
      fields = line.strip().split()
      if len(fields) > 0 and fields[0].startswith("/dev"):
        devices.append(fields[0].strip())
        mounts.append(fields[2].strip())

    # discover network interfaces
    for line in execute_command("ip a")[1].split("\n"):
      if re.match("^[0-9]+:", line):
        fields = line.strip().split()
        interfaces.append(fields[1][0:-1])

    for device in devices:
      for op in ["read", "write"]:
        self._append_config_key("vfs.dev.%s[%s]" % (op, device))
    for mount in mounts:
      for op in ["used", "free"]:
        self._append_config_key("vfs.fs.size[%s,%s]" % (mount, op))
    for interface in interfaces:
      for op in ["in", "out"]:
        self._append_config_key("net.if.%s[%s]" % (op, interface))

  def startup(self, config=None):
    try:
      self._config = config

      # Make sure that zabbix agent is running.
      zabbix_agentd = search_running_processes('zabbix_agentd')
      if not zabbix_agentd:
        nuoca_log(logging.ERROR, "Zabbix agent daemon is not running.")
        return False

      # Make sure that zabbix_get is installed.
      command = "which zabbix_get"
      (exit_code, stdout, stderr) = execute_command(command)
      if exit_code != 0 or 'zabbix_get' not in stdout:
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

      if config['autoDiscoverMonitors']:
        self._auto_discover_monitors()

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
    collected_values = super(MPZabbix, self).collect(collection_interval)
    try:
      for key in self._config['keys']:
        command = "zabbix_get -s localhost -k %s" % key
        (exit_code, stdout, stderr) = execute_command(command)
        if exit_code != 0:
          nuoca_log(logging.ERROR, "Problem with zabbix_get command.")
          return False
        if stdout.strip() is 'ZBX_NOTSUPPORTED':
          nuoca_log(logging.WARNING, "zabbix_get on key '%s' returned ZBX_NOTSUPPORTED" % key)
        collected_values[key] = coerce_numeric(stdout.strip())
      rval.append(collected_values)
    except Exception as e:
      nuoca_log(logging.ERROR, str(e))
    return rval
