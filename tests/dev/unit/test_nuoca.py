from __future__ import print_function

import os
import unittest
import logging
import nuoca_util
import nuoca


class TestNuoCA(unittest.TestCase):

  def setUp(self):
    super(TestNuoCA, self).setUp()
    self._topdir = nuoca_util.get_nuoca_topdir()
    self._plugin_dir = os.path.join(self._topdir, "plugins")
    self._config_dir = os.path.join(self._topdir, "tests", "dev", "configs")

  def test_dirs(self):
    self.assertTrue(os.path.isdir(self._topdir))
    self.assertTrue(os.path.isdir(self._plugin_dir))
    self.assertTrue(os.path.isdir(self._config_dir))

  def test_empty_config(self):
    nuoca_obj = \
        nuoca.NuoCA(
            config_file=os.path.join(self._config_dir, "empty.yml"),
            collection_interval=1,
            log_level=logging.ERROR,
            plugin_dir=self._plugin_dir,
            self_test=True,
            starttime=None
        )
    self.assertIsNotNone(nuoca_obj)
    nuoca_obj.config.SELFTEST_LOOP_COUNT = 1
    nuoca_obj.start()
    nuoca_obj.shutdown(timeout=0)

  def test_counter_printer(self):
    """
    Test using the mpCounterPlugin and mpPrinterPlugin
    """
    nuoca_obj = nuoca.NuoCA(
        config_file=os.path.join(self._config_dir, "counter.yml"),
        collection_interval=1,
        log_level=logging.ERROR,
        plugin_dir=self._plugin_dir,
        self_test=True,
        starttime=None
    )
    self.assertIsNotNone(nuoca_obj)
    nuoca_obj.config.SELFTEST_LOOP_COUNT = 2
    nuoca_obj.start()
    nuoca_obj.shutdown(timeout=1)
