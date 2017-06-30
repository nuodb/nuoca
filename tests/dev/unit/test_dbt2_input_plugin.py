from __future__ import print_function

import unittest
import nuoca_util

from tests.dev.plugins.input.mpDbt2InputPlugin import MPDbt2InputPlugin


class TestInputPlugins(unittest.TestCase):
  def _MPDbt2InputPluginTest(self):
    nuoca_util.initialize_logger()
    dbt2_plugin = MPDbt2InputPlugin(None)
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
    self._MPDbt2InputPluginTest()


