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

import hashlib
import json
import logging
import os
import re
import socket
import subprocess
import threading

from calendar import timegm
from dateutil.parser import parse as date_parse
from nuoca_plugin import NuocaMPInputPlugin
from nuoca_util import nuoca_log

# Logstash plugin
#
# Logstash plugin configuration:
#
# - Logstash:
#    description: Description for your plugin config.
#    logstashBin: full path to the logstash executable (required)
#    logstashConfig: full path to a logstash config file. (required)
#    logstashOptions: logstash command line options. (optional)
#      This logstash plug always runs logstash with --node.name and
#      --path.config command line arguments.  If you want any option
#      logstash arguments, then set, space separated in logstashOptions.
#    logstashInputFilePath: full path to an optional logstash input file.
#      (optional)
#       If this is set, then a shell environment variable
#       LOGSTASH_INPUT_FILE_PATH is set to this value.  This provides
#       a convient way to parameterize the input file for logstash
#       config file.
#    logstashSincedbPath: full path to logstash sincedb file. (optional)
#      if logstashSincedbPath is not set, and logstashInputFilePath is set,
#      then logstashSincedbPath is set to:
#          $HOME/.sincedb_<MD5 hash of logstashInputFilePath>
#      If this is set, then a shell environment variable LOGSTASH_SINCEDB_PATH
#      is set to this value.  In this way, you can parameterize the
#      file.sincedb_path in a logstash config file.
#


class LogstashPlugin(NuocaMPInputPlugin):
  def __init__(self, parent_pipe):
    super(LogstashPlugin, self).__init__(parent_pipe, 'Logstash')
    self._config = None
    self._enabled = False
    self._logstash_bin = None
    self._logstash_config = None
    self._nuocaCollectionName = None
    self._logstash_thread = None
    self._process_thread = None
    self._logstash_subprocess = None
    self._logstash_sincedb_path = None
    self._logstash_options = None
    self._line_counter = 0
    self._lines_processed = 0
    self._local_hostname = socket.gethostname()
    self._host_uuid_shortname = False
    self._host_shortid = None
    self._logstash_collect_queue = []

  @property
  def logstash_collect_queue(self):
    return self._logstash_collect_queue

  def _run_logstash_thread(self):
    self._logstash_subprocess = None
    if 'logstashInputFilePath' in self._config:
      os.environ["LOGSTASH_INPUT_FILE_PATH"] = \
        self._config['logstashInputFilePath']
    if self._logstash_sincedb_path:
      os.environ["LOGSTASH_SINCEDB_PATH"] = self._logstash_sincedb_path
    try:
      popen_args = [self._logstash_bin,
                    '--node.name', self._nuocaCollectionName,
                    "--path.config", self._logstash_config]
      if self._logstash_options:
        popen_args.extend(self._logstash_options)
      self._logstash_subprocess = \
        subprocess.Popen(popen_args, stdout=subprocess.PIPE)
    except Exception as e:
      msg = "logstash process: %s" % str(e)
      msg += "\nlogstash_bin: %s" % self._logstash_bin
      msg += "\nlogstash_config: %s" % self._logstash_config
      nuoca_log(logging.ERROR, msg)
      return

    try:
      while self._enabled:
        json_object = None
        line = self._logstash_subprocess.stdout.readline()
        if line:
          self._line_counter += 1
          try:
            json_object = json.loads(line)
          except ValueError:
            # These messages are typical log messages about logstash itself
            # which are written to stdout.  Just write them to the nuoca.log
            msg = "logstash message: %s" % line
            nuoca_log(logging.INFO, msg)
          if json_object:
            self._logstash_collect_queue.append(json_object)
      nuoca_log(logging.INFO,
        "Logstash plugin run_logstash_thread "
        "completed %s lines" % str(self._line_counter))
    except Exception as e:
      msg = "logstash process: %s" % str(e)
      nuoca_log(logging.ERROR, msg)
      pass

    try:
      if self._logstash_subprocess:
        self._logstash_subprocess.kill()
    except Exception as e:
      msg = "Excpetion trying to kill logstash process: %s" % str(e)
      nuoca_log(logging.ERROR, msg)

  def startup(self, config=None):
    uuid_hostname_regex = \
      '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}-'
    try:
      self._config = config

      # Validate the configuration.
      #   logstash_bin: full path to the logstash executable
      #   logstash_config: full path to a logstash config file.
      required_config_items = ['logstashBin', 'logstashConfig']
      if not self.has_required_config_items(config, required_config_items):
        return False
      nuoca_log(logging.INFO, "Logstash plugin config: %s" %
                str(self._config))

      self._logstash_bin = os.path.expandvars(config['logstashBin'])
      if not os.path.isfile(self._logstash_bin):
        msg = "Unable to find 'logstashBin' file: %s" % self._logstash_bin
        nuoca_log(logging.ERROR, msg)
        return False

      self._logstash_config = os.path.expandvars(config['logstashConfig'])
      if not os.path.isfile(self._logstash_config):
        msg = "Unable to find 'logstashConfig' file: %s" % \
              self._logstash_config
        nuoca_log(logging.ERROR, msg)
        return False

      if 'logstashSincedbPath' in config:
        self._logstash_sincedb_path = \
          os.path.expandvars(config['logstashSincedbPath'])
      else:
        if 'logstashInputFilePath' in config:
          nuoca_log(logging.INFO, "Logstash Plugin Input File Path: %s" %
                    str(config['logstashInputFilePath']))
          hexdigest = hashlib.md5(config['logstashInputFilePath']).hexdigest()
          self._logstash_sincedb_path = \
            "%s/.sincedb_%s" % (os.environ['HOME'], hexdigest)

      nuoca_log(logging.INFO, "Logstash Plugin sincedb_path: %s" %
                str(self._logstash_sincedb_path))

      if 'logstashOptions' in config:
        logstash_options = os.path.expandvars(config['logstashOptions'])
        self._logstash_options = logstash_options.split(' ')

      if 'nuocaCollectionName' in config:
        self._nuocaCollectionName = config['nuocaCollectionName']

      # For Coach hostnames in the format: uuid-shortId
      if 'host_uuid_shortname' in config:
        self._host_uuid_shortname = config['host_uuid_shortname']

      if self._host_uuid_shortname:
        m2 = re.search(uuid_hostname_regex, self._local_hostname)
        if m2:
          self._host_shortid = self._local_hostname[37:]

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
    if self._logstash_subprocess:
      self._logstash_subprocess.terminate()
      self._logstash_subprocess = None
    if self._process_thread:
      self._process_thread.join()

  def collect(self, collection_interval):
    rval = None
    try:
      nuoca_log(logging.DEBUG,
                "Called collect() in Logstash Plugin process")
      base_values = super(LogstashPlugin, self).\
        collect(collection_interval)
      base_values['Hostname'] = self._local_hostname
      if self._host_shortid:
        base_values['HostShortID'] = self._host_shortid
      if self._nuocaCollectionName:
        base_values['nuocaCollectionName'] = self._nuocaCollectionName
      rval = []
      collection_count = len(self._logstash_collect_queue)
      if not collection_count:
        return rval

      for i in range(collection_count):
        collected_dict = self._logstash_collect_queue.pop(0)
        collected_dict.update(base_values)
        if 'timestamp' in collected_dict:
          dt = date_parse(collected_dict['timestamp'])
          epoch_seconds = timegm(dt.timetuple())
          epoch_millis = epoch_seconds * 1000 + dt.microsecond / 1000
          collected_dict['TimeStamp'] = epoch_millis
        rval.append(collected_dict)
    except Exception as e:
      nuoca_log(logging.ERROR, str(e))
    return rval
