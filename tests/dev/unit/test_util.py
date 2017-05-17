from __future__ import print_function

import os
import sys
import unittest
import nuoca_util
import logging


class TestUtilRandomID(unittest.TestCase):
  def runTest(self):
    self.assertTrue(True)
    tid = nuoca_util.randomid()
    self.assertTrue(tid)


class TestNuoCATopDir(unittest.TestCase):
  def runTest(self):
    topdir = nuoca_util.get_nuoca_topdir()
    self.assertTrue(topdir)
    self.assertTrue(os.path.exists(topdir))
    etc_dir = os.path.join(topdir, 'etc')
    self.assertTrue(os.path.exists(etc_dir))


class TestUtilLogging(unittest.TestCase):
  # noinspection PyMethodMayBeStatic
  def runTest(self):
    nuoca_util.nuoca_set_log_level(logging.INFO)
    nuoca_util.nuoca_log(logging.INFO, "Info message")
    nuoca_util.nuoca_logging_shutdown()


if __name__ == '__main__':
  sys.exit(unittest.main())
