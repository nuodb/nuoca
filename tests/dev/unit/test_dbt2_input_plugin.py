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

from __future__ import print_function

import unittest
import nuoca_util

from plugins.input.Dbt2Plugin import Dbt2Plugin


class TestInputPlugins(unittest.TestCase):
  def _Dbt2InputPluginTest(self):
    nuoca_util.initialize_logger("/tmp/nuoca.test.log")
    dbt2_plugin = Dbt2Plugin(None)
    self.assertIsNotNone(dbt2_plugin)

    # startup should fail if directory not specified.
    config = {}
    startup_rval = dbt2_plugin.startup(config)
    self.assertFalse(startup_rval)

    # startup should pass if directory doesn't exist but fail on collect
    config = {'dbt2_log_dir': '/does-not-exist'}
    startup_rval = dbt2_plugin.startup(config)
    self.assertTrue(startup_rval)
    resp_values = dbt2_plugin.collect(10)
    self.assertIsNone(resp_values)

    # test with existing log dir containing no logs
    config = {'dbt2_log_dir': '/tmp'}
    startup_rval = dbt2_plugin.startup(config)
    self.assertTrue(startup_rval)
    resp_values = dbt2_plugin.collect(10)
    self.assertIsNone(resp_values)

    # Rewrite some mix logs with current timestamps
    # log_dir = '/tmp/dbt2-logs'
    # shutil.rmtree(log_dir)
    # if not os.path.exists(log_dir):
    #   os.makedirs(log_dir)
    # orig_mix_log_dir = os.path.join(nuoca_util.get_nuoca_topdir(),
    #                                 "tests/dev/unit/dbt2-data")
    # start_time = time.time() - 30
    # for num in range(1, 4):
    #   mix_filename = 'mix.' + str(num) + '.log'
    #   with open(os.path.join(orig_mix_log_dir, mix_filename)) as mixlog:
    #     with open(os.path.join(log_dir, mix_filename))
    #     for line in mixlog:
    #       line_list = line.split(',')
    #       new_time = float(line_list[0]) - 30.0
    #       line_list[0] = str(new_time)
    # for file in os.listdir(os.path.join(topdir, "tests/dev/unit/dbt2-data"))
    # os.chdir(data_dir)

    dbt2_plugin.shutdown()

  def runTest(self):
    self._Dbt2InputPluginTest()


