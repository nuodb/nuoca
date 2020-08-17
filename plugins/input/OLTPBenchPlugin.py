# (C) Copyright NuoDB, Inc. 2017-2020
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.

import logging
from pynuoca.nuoca_plugin import NuocaMPInputPlugin
from pynuoca.nuoca_util import nuoca_log, coerce_numeric
import subprocess
import re
import os


class OLTPBenchPlugin(NuocaMPInputPlugin):
    def __init__(self, parent_pipe):
        super(OLTPBenchPlugin, self).__init__(parent_pipe, 'OLTPBench')
        self._config = None
        self._last_tps = None
        self._last_ltc = None
        self._log_file = None
        self._log_dir = None
        self._metrics_dict = None

    def startup(self, config=None):
        nuoca_log(logging.INFO, "Setting up oltpbenchplugin..")
        try:
            self._config = config
            required_config_items = ['log_dir', 'log_file']
            if not self.has_required_config_items(config, required_config_items):
                return False
            for var in 'log_file', 'log_dir':
                exec ("self._" + var + " = str(config['" + var + "'])")
            return True
        except Exception as e:
            nuoca_log(logging.ERROR, str(e))
            return False

    def shutdown(self):
        pass

    def run_parser(self):
        full_logpath = os.path.join(self._log_dir, self._log_file)
        cmd = "printf 'tps=\"'; \
printf $(grep 'Throughput: ' {} | tail -1 | sed 's/.*Throughput: //; s/ Tps//')\\\"; \
printf ' latency_average=\"'; \
printf $(grep 'Latency Average: ' {} | tail -1 | sed 's/.*Latency Average: //; s/ ms//')\\\";".format(full_logpath,
                                                                                                      full_logpath)
        nuoca_log(logging.DEBUG, "Running command: %s" % (format(cmd)))
        try:
            output = subprocess.check_output(
                cmd, stderr=subprocess.STDOUT, shell=True)
        except subprocess.CalledProcessError as e:
            nuoca_log(logging.ERROR, "run_parser ERROR: RC: %d, ERR: %s" %
                      (e.returncode, e.output))
            return None
        nuoca_log(logging.DEBUG, "Parser output: %s" % (format(output)))
        self._metrics_dict = dict(re.findall(r'(\w+)="([^"]+)"', output))
        if self._metrics_dict["tps"] == self._last_tps:
            self._metrics_dict["tps"] = None
        else:
            self._last_tps = self._metrics_dict["tps"]
        if self._metrics_dict["latency_average"] == self._last_ltc:
            self._metrics_dict["latency_average"] = None
        else:
            self._last_ltc = self._metrics_dict["latency_average"]

        return True

    def collect(self, collection_interval):
        rval = None
        try:
            nuoca_log(logging.DEBUG,
                      "Called collect() in OLTPBenchPlugin process...")
            collected_values = \
                super(OLTPBenchPlugin, self).collect(collection_interval)
            rval = []
            rval.append(collected_values)
            if not self.run_parser():
                return None
            if self._metrics_dict:
                for metric_item in self._metrics_dict:
                    if self._metrics_dict[metric_item]:
                        collected_values[metric_item] = \
                            coerce_numeric(self._metrics_dict[metric_item])
        except Exception as e:
            nuoca_log(logging.ERROR, str(e))
        return rval
