# (C) Copyright NuoDB, Inc. 2017-2018
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.

from __future__ import print_function

import os
import unittest
import logging
from pynuoca import nuoca_util
from pynuoca import nuoca


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


  def test_counter_with_env_vars(self):
    """
    Validate env var using counter plugin
    """
    nuoca_obj = nuoca.NuoCA(
      config_file=os.path.join(self._config_dir, "counter_with_env_vars.yml"),
      collection_interval=1,
      log_level=logging.ERROR,
      plugin_dir=self._plugin_dir,
      self_test=True,
      starttime=None
    )
    self.assertIsNotNone(nuoca_obj)
    nuoca_obj.config.SELFTEST_LOOP_COUNT = 1
    nuoca_obj.start()
    nuoca_obj.shutdown(timeout=1)
    lines = None
    with open('/tmp/nuoca_counter_with_env_vars.log') as f:
      lines = f.readlines()
    self.assertTrue(lines != None, msg="Log lines not found.")
    found = False
    for line in lines:
      if (line.endswith('Env: FOO=BAR\n')):
        found = True
    self.assertTrue(found, msg="Environment Variable FOO=BAR was not found.")