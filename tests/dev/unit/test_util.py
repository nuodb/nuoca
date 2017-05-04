from __future__ import print_function

import os
import sys
import unittest
import nuoca_util
import logging


class TestUtilRandomID(unittest.TestCase):
  def runTest(self):
    self.assertTrue(True)
    id = nuoca_util.randomid()
    self.assertTrue(id)


class TestNuoCATopDir(unittest.TestCase):
  def runTest(self):
    topdir = nuoca_util.get_nuoca_topdir()
    self.assertTrue(topdir)
    self.assertTrue(os.path.exists(topdir))
    etc_dir = os.path.join(topdir, 'etc')
    self.assertTrue(os.path.exists(etc_dir))


class TestUtilLogging(unittest.TestCase):
  def runTest(self):
    nuoca_util.nuoca_log(logging.INFO, "Info message")


if __name__ == '__main__':
  sys.exit(unittest.main())
