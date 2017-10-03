import logging
import os
import re
import socket
import subprocess
import threading
import json
from dateutil.parser import parse as date_parse
from calendar import timegm

from Queue import Queue, Empty

from nuoca_plugin import NuocaMPInputPlugin
from nuoca_util import nuoca_log

# Logstash plugin
#
# Example Logstash plugin configuration:
#
# - Logstash:
#    description : Collection from Logstash.
#    logstashBin: full path to the logstash executable (required)
#    logstashConfig: full path to a logstash config file. (required)
#    logFile: full path to input logfile(s) (optional)


class MPLogstash(NuocaMPInputPlugin):
  def __init__(self, parent_pipe):
    super(MPLogstash, self).__init__(parent_pipe, 'Logstash')
    self._config = None
    self._enabled = False
    self._logstash_bin = None
    self._logstash_config = None
    self._logfile = None
    self._nuocaCollectionName = None
    self._logstash_thread = None
    self._process_thread = None
    self._agentLogQueue = Queue()
    self._tail_subprocess = None
    self._line_counter = 0
    self._lines_processed = 0
    self._local_hostname = socket.gethostname()
    self._host_uuid_shortname = False
    self._host_shortid = None
    self._nuoAdminAgentLog_collect_queue = []

  @property
  def nuoAdminAgentLog_collect_queue(self):
    return self._nuoAdminAgentLog_collect_queue

  def _run_logstash_thread(self):
    self._tail_subprocess = None
    try:
      self._tail_subprocess = \
        subprocess.Popen([self._logstash_bin, "--path.config",
                          self._logstash_config],
                          stdout=subprocess.PIPE)
    except Exception as e:
      # TODO: Log errors and quit.
      pass

    try:
      while self._enabled:
        json_object = None
        line = self._tail_subprocess.stdout.readline()
        if line:
          self._line_counter += 1
          try:
            json_object = json.loads(line)
          except ValueError, e:
            msg = "logstash message: %s" % line
            nuoca_log(logging.INFO, msg)
          if json_object:
            self._nuoAdminAgentLog_collect_queue.append(json_object)
      nuoca_log(logging.INFO,
        "Logstash plugin run_logstash_thread "
        "completed %s lines" % str(self._line_counter))
    except Exception as e:
      # TODO: Log errors and quit.
      pass

    try:
      self._tail_subprocess.kill()
    except Exception as e:
      pass

  def startup(self, config=None):
    uuid_hostname_regex = \
      '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}-'
    try:
      self._config = config

      # Validate the configuration.
      #    logstash_bin: full path to the logstash exeutable
      #    logstash_config: full path to a logstash config file.
      required_config_items = ['logstashBin', 'logstashConfig']
      if not self.has_required_config_items(config, required_config_items):
        return False
      nuoca_log(logging.INFO, "Logstash plugin config: %s" %
                str(self._config))

      self._logstash_bin = os.path.expandvars(config['logstashBin'])
      self._logstash_config = os.path.expandvars(config['logstashConfig'])

      # For Coach hostnames in the format: uuid-shortId
      if 'host_uuid_shortname' in config:
        self._host_uuid_shortname = config['host_uuid_shortname']

      if 'nuocaCollectionName' in config:
        self._nuocaCollectionName = config['nuocaCollectionName']

      if self._host_uuid_shortname:
        m2 = re.search(uuid_hostname_regex, self._local_hostname)
        if m2:
          self._host_shortid = self._local_hostname[37:]

      if 'logFile' in config:
        self._logfile = os.path.expandvars(config['logFile'])

      self._enabled = True
      self._logstash_thread = \
        threading.Thread(target=self._run_logstash_thread)
      self._logstash_thread.daemon = True
      self._logstash_thread.start()

      return True

    except Exception as e:
      nuoca_log(logging.ERROR, "Logstash Plugin: %s" % str(e))
      return False

  def shutdown(self):
    self.enabled = False
    if self._tail_subprocess:
      self._tail_subprocess.terminate()
      self._tail_subprocess = None
    if self._process_thread:
      self._process_thread.join()

  def collect(self, collection_interval):
    rval = None
    try:
      nuoca_log(logging.DEBUG,
                "Called collect() in Logstash Plugin process")
      base_values = super(MPLogstash, self).\
        collect(collection_interval)
      base_values['Hostname'] = self._local_hostname
      if self._host_shortid:
        base_values['HostShortID'] = self._host_shortid
      if self._nuocaCollectionName:
        base_values['nuocaCollectionName'] = self._nuocaCollectionName
      rval = []
      collection_count = len(self._nuoAdminAgentLog_collect_queue)
      if not collection_count:
        return rval

      for i in range(collection_count):
        collected_dict = self._nuoAdminAgentLog_collect_queue.pop(0)
        collected_dict.update(base_values)
        if 'timestamp' in collected_dict:
          dt = date_parse(collected_dict['timestamp'])
          collected_dict['TimeStamp'] = timegm(dt.timetuple())
        rval.append(collected_dict)
    except Exception as e:
      nuoca_log(logging.ERROR, str(e))
    return rval
