# (C) Copyright NuoDB, Inc. 2017-2020
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.

import logging
import os
import time
from math import sqrt
from stat import ST_CTIME

from pynuoca.nuoca_plugin import NuocaMPInputPlugin
from pynuoca.nuoca_util import nuoca_log


class Dbt2Plugin(NuocaMPInputPlugin):
    def __init__(self, parent_pipe):
        super(Dbt2Plugin, self).__init__(parent_pipe, 'Dbt2')
        self._dbt2_log_dir = None

    def startup(self, config=None):
        try:
            self._dbt2_log_dir = None
            required_config_items = ['dbt2_log_dir']
            if not self.has_required_config_items(config, required_config_items):
                return False
            self._dbt2_log_dir = config['dbt2_log_dir']
            return True
        except Exception as e:
            nuoca_log(logging.ERROR, str(e))
        return False

    def shutdown(self):
        pass

    @staticmethod
    def read_chunk(parser, fh, up_to_time, should_keep):
        line = fh.readline()
        if line:
            try:
                line_time = float(line.split(',')[0])
            except:
                line_time = 0
        else:
            return
        while line_time <= up_to_time:
            if should_keep:
                parser.process_mix_line(line)
            line = fh.readline()
            if not line:
                break
            try:
                line_time = float(line.split(',')[0])
            except:
                line_time = 0

    def collect(self, collection_interval):
        rval = None
        try:
            dbt2_parser = Dbt2ResultsParser()
            # Find two most recent mix logs
            if not os.path.exists(self._dbt2_log_dir):
                nuoca_log(logging.WARNING,
                          "DBT2 log path not found (" + self._dbt2_log_dir + ").")
            else:
                entries = (os.path.join(self._dbt2_log_dir, fn) for fn in
                           os.listdir(self._dbt2_log_dir) if
                           fn.startswith('mix'))
                entries = ((os.stat(path), path) for path in entries)
                entries = list(sorted(((stat[ST_CTIME], path) for stat,
                                                                  path in entries)))
                if len(entries) < 2:
                    nuoca_log(logging.INFO, "DBT2: There are not two mix logs yet.")
                else:
                    most_recent = entries[-1][1]
                    second_recent = entries[-2][1]
                    end_time = time.time()
                    start_time = end_time - collection_interval

                    with open(second_recent, 'r') as mixlog:
                        self.read_chunk(dbt2_parser, mixlog, start_time, False)
                        self.read_chunk(dbt2_parser, mixlog, end_time, True)

                    with open(most_recent, 'r') as mixlog:
                        self.read_chunk(dbt2_parser, mixlog, start_time, False)
                        self.read_chunk(dbt2_parser, mixlog, end_time, True)

                    metrics = super(Dbt2Plugin, self).collect(collection_interval)
                    metrics = dbt2_parser.process_metrics(metrics)
                    if metrics is not None:
                        rval = [metrics]
        except Exception as e:
            nuoca_log(logging.ERROR, str(e))
        return rval


"""
Mostly copied from dbt2's dbt2-post-process
Removed concept of rampup and steady-state since this is for real-time
monitoring
Removed tracking all metrics except New Order for efficiency.
"""


class Dbt2ResultsParser:
    def __init__(self):
        self.start_time = 0
        self.end_time = 0
        self.transactions = 0
        self.rollbacks = 0
        self.errors = 0
        self.sum_latencies = 0
        self.sum_latencies_sq = 0
        self.parse_errors = 0

    def process_mix_line(self, line):
        try:
            line_values = line.split(',')
            line_timestamp = int(line_values[0])
            if len(line_values) < 2 or line_values[1] == 'TERMINATED':
                return
            else:
                line_trans_type = line_values[1]
            if len(line_values) != 5:
                # probably result of partial buffered line
                self.parse_errors += 1
                return

            if self.start_time == 0:
                self.start_time = line_timestamp

            line_trans_rc = line_values[2]
            if line_trans_type == 'n' and line_trans_rc in ['C', 'R', 'E']:
                self.transactions += 1
                if line_trans_rc == 'R':
                    self.rollbacks += 1
                elif line_trans_rc == 'E':
                    self.errors += 1
                    return

                line_lat = float(line_values[3])
                self.sum_latencies += line_lat
                self.sum_latencies_sq += line_lat * line_lat
                self.end_time = line_timestamp
        except:
            self.parse_errors += 1
            return

    def process_metrics(self, metrics):
        if self.parse_errors > 0:
            nuoca_log(logging.INFO,
                      "DBT2: process_metrics: there were " + self.parse_errors +
                      " parse errors reading the logs")
        duration = float(self.end_time - self.start_time)
        if self.transactions > 1 and duration > 0:
            lat_avg = self.sum_latencies / self.transactions
            metrics['notpm'] = float(self.transactions) * 60.0 / duration
            metrics['lat_avg'] = float(lat_avg)
            # Estimating 90th percentile from standard deviation
            stddev = sqrt((self.sum_latencies_sq / self.transactions) -
                          (lat_avg * lat_avg))
            metrics['lat_90th'] = float(lat_avg + stddev * 1.28)
            return metrics
        else:
            return None
