# (C) Copyright NuoDB, Inc. 2017-2020
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.

import hashlib
import json
import logging
import os
import re
import socket
import subprocess
import threading
import time

from datetime import datetime
from dateutil.parser import parse as date_parse
from pynuoca.nuoca_plugin import NuocaMPInputPlugin
from pynuoca.nuoca_util import nuoca_log
from pynuoca.nuoca_util import to_bool


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
#    dropThrottledEvents: boolean (optional, default=false)
#      if the is set, then drop any events with the "throttled" tag.
#
#  Users can set 'timestamp_iso8601' in their collection to force the event
#  timestamp to become the epoch_millis (the number of milliseconds since
#  Unix Epoch)
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
        self._drop_throttled = False
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
        msg = "Env: %s=%s" % ('NUOCA_HOME', os.environ['NUOCA_HOME'])
        nuoca_log(logging.INFO, msg)

        if self._logstash_sincedb_path:
            msg = "Env: LOGSTASH_SINCEDB_PATH=%s" % \
                  self._logstash_sincedb_path
            nuoca_log(logging.INFO, msg)
            os.environ["LOGSTASH_SINCEDB_PATH"] = self._logstash_sincedb_path
        try:
            popen_args = [self._logstash_bin,
                          '--node.name', self._nuocaCollectionName,
                          "--path.config", self._logstash_config]
            if self._logstash_options:
                popen_args.extend(self._logstash_options)
            msg = "Starting %s --node.name %s --path.config %s" % \
                  (self._logstash_bin,
                   self._nuocaCollectionName,
                   self._logstash_config)
            for item in self._logstash_options:
                msg += " %s" % str(item)
            nuoca_log(logging.INFO, msg)
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
                if not line:
                    # Check to see if the logstash process failed unexpectedly
                    if self._logstash_subprocess.poll() != None:
                        self._enabled = False
                        msg = "logstash process has unexpectedly exited, returncode:%s" % \
                              self._logstash_subprocess.returncode
                        nuoca_log(logging.ERROR, msg)
                else:
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
            msg = "Exception trying to kill logstash process: %s" % str(e)
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
            nuoca_log(logging.INFO, "logstashConfig: %s" % str(self._logstash_config))

            logstash_input_file_path = '/dev/null'
            logstash_input_file_path2 = '/dev/null'

            if 'logstashInputFilePath' in self._config:
                if isinstance(self._config['logstashInputFilePath'], str):
                    msg = "Env: LOGSTASH_INPUT_FILE_PATH=%s" % \
                          self._config['logstashInputFilePath']
                    nuoca_log(logging.INFO, msg)
                    logstash_input_file_path = \
                        os.path.expandvars(self._config['logstashInputFilePath'])

            if isinstance(self._config['logstashInputFilePath'], list):
                if len(self._config['logstashInputFilePath']) > 2:
                    msg = "logstashInputFilePath list has more than 2 elements: %s" % \
                          self._config['logstashInputFilePath']
                    nuoca_log(logging.ERROR, msg)
                    return
                else:
                    msg = "Env: LOGSTASH_INPUT_FILE_PATH=%s" % \
                          self._config['logstashInputFilePath'][0]
                    nuoca_log(logging.INFO, msg)
                    logstash_input_file_path = \
                        os.path.expandvars(self._config['logstashInputFilePath'][0])
                    logstash_input_file_path2 = \
                        os.path.expandvars(self._config['logstashInputFilePath'][1])

            os.environ["LOGSTASH_INPUT_FILE_PATH"] = logstash_input_file_path
            msg = "Env: LOGSTASH_INPUT_FILE_PATH=%s" % logstash_input_file_path
            nuoca_log(logging.INFO, msg)
            os.environ["LOGSTASH_INPUT_FILE_PATH2"] = logstash_input_file_path2
            msg = "Env: LOGSTASH_INPUT_FILE_PATH2=%s" % logstash_input_file_path2
            nuoca_log(logging.INFO, msg)
            if 'logstashSincedbPath' in config:
                self._logstash_sincedb_path = \
                    os.path.expandvars(config['logstashSincedbPath'])
            else:
                if 'logstashInputFilePath' in config:
                    nuoca_log(logging.INFO, "Logstash Plugin Input File Path: %s" %
                              str(config['logstashInputFilePath']))
                    hexdigest = hashlib.md5(str(config['logstashInputFilePath'])).hexdigest()
                    self._logstash_sincedb_path = \
                        "%s/.sincedb_%s" % (os.environ['HOME'], hexdigest)

            nuoca_log(logging.INFO, "Logstash Plugin sincedb_path: %s" %
                      str(self._logstash_sincedb_path))

            if 'logstashOptions' in config:
                logstash_options = os.path.expandvars(config['logstashOptions'])
                self._logstash_options = logstash_options.split(' ')

            if 'dropThrottledEvents' in config:
                self._drop_throttled = to_bool(config['dropThrottledEvents'])

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
        self._enabled = False
        if self._logstash_subprocess:
            self._logstash_subprocess.terminate()
            self._logstash_subprocess = None
        if self._process_thread:
            self._process_thread.join()

    def collect(self, collection_interval):
        rval = None
        if not self._enabled:
            return 0
        dt1 = datetime.utcnow()
        drop_throttled_count = 0
        try:
            nuoca_log(logging.DEBUG,
                      "Called collect() in Logstash Plugin process")
            base_values = super(LogstashPlugin, self). \
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
                if self._drop_throttled and \
                        'tags' in collected_dict and \
                        'throttled' in collected_dict['tags']:
                    drop_throttled_count += 1
                    continue
                if 'timestamp_iso8601' in collected_dict:
                    dt1 = date_parse(collected_dict['timestamp_iso8601'])
                    tt = dt1.timetuple()
                    # When processing the ISO8601 time string, there is no way to
                    # determine local daylight saving time from the timestring, so the
                    # call to dt1.timetuple() sets tm_idst=0.  But we want to force
                    # time.mktime() to consider daylight savings time in it's calculation
                    # so we need to set tm_isdst=-1.  The Python time tuple 'tt' is
                    # read-only, so I made a writeable list 'tt_writeable' to set
                    # tm_isdst (the 9th element in the list) to -1.  And then create
                    # a new time tuple 'tt' from the writeable version.
                    tt_writeable = list(tt)
                    tt_writeable[8] = -1
                    tt = time.struct_time(tuple(tt_writeable))
                    epoch_seconds = int(time.mktime(tt))
                    epoch_millis = epoch_seconds * 1000 + dt1.microsecond / 1000
                    collected_dict['TimeStamp'] = epoch_millis
                rval.append(collected_dict)

            if self._drop_throttled and drop_throttled_count > 0:
                msg = "Logstash (%s) dropping %d throttled events" % \
                      (self._nuocaCollectionName, drop_throttled_count)
                nuoca_log(logging.INFO, msg)
                drop_throttle_event = {}
                epoch_seconds = int(time.mktime(dt1.timetuple()))
                epoch_millis = epoch_seconds * 1000 + dt1.microsecond / 1000
                drop_throttle_event['TimeStamp'] = epoch_millis
                drop_throttle_event['logger'] = 'NuoCA'
                drop_throttle_event['loglevel'] = 'INFO'
                drop_throttle_event['message'] = msg
                rval.append(drop_throttle_event)

        except Exception as e:
            nuoca_log(logging.ERROR, str(e))
        return rval
