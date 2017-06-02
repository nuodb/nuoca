from __future__ import print_function

import os
import unittest
import nuoca_util
import nuoca


class TestNuoCARunFunction(unittest.TestCase):

  def setUp(self):
    super(TestNuoCARunFunction, self).setUp()
    self._topdir = nuoca_util.get_nuoca_topdir()
    self._plugin_dir = os.path.join(self._topdir, "tests", "dev", "plugins")
    self._config_dir = os.path.join(self._topdir, "tests", "dev", "configs")

  def test_nuoca_function(self):
    self.assertTrue(os.path.isdir(self._topdir))
    self.assertTrue(os.path.isdir(self._plugin_dir))
    self.assertTrue(os.path.isdir(self._config_dir))
    nuoca.nuoca_run(
        config_file=os.path.join(self._config_dir, "counter_quick.yaml"),
        collection_interval=1,
        log_level="ERROR",
        plugin_dir=self._plugin_dir,
        self_test=True,
        starttime=nuoca_util.nuoca_gettimestamp() + 3,
        verbose=False,
        output_values=None
    )
