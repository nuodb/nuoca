# (C) Copyright NuoDB, Inc. 2017-2018
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.

from __future__ import print_function

import os
import shutil
import unittest
import nuoca_util
import insights


class TestGetDomainAuth(unittest.TestCase):
  def runTest(self):
    os.environ['DOMAIN_USER'] = 'a_domain_username'
    os.environ['DOMAIN_PASSWORD'] = 'a_domain_password'
    auth = insights.get_legacy_domain_auth()
    self.assertTrue(auth)
    self.assertEquals(auth.username, os.environ['DOMAIN_USER'])
    self.assertEquals(auth.password, os.environ['DOMAIN_PASSWORD'])


class TestGetDomainSession(unittest.TestCase):
  def runTest(self):
    # TODO
    pass

class TestCheckEnvVar(unittest.TestCase):
  def runTest(self):
    test_dir = os.path.join(os.path.sep, 'tmp', 'test_insights_tmpdir')
    os.environ['TEST_DIR'] = test_dir
    shutil.rmtree(test_dir, ignore_errors=True)
    # TODO - Test case where 'test_dir' does not exist
    os.mkdir(test_dir)
    insights.check_env_var('TEST_DIR', check_dir=False)
    insights.check_env_var('TEST_DIR', check_dir=True)
    shutil.rmtree(test_dir, ignore_errors=True)

class TestCheckEnvrionment(unittest.TestCase):
  def runTest(self):
    os.environ['NUODB_HOME'] = os.path.join(os.path.sep, 'opt', 'nuodb')
    os.environ['NUODB_CFGDIR'] = os.path.join(os.path.sep, 'etc', 'nuodb')
    os.environ['NUODB_VARDIR'] = os.path.join(os.path.sep, 'var', 'opt', 'nuodb')
    os.environ['NUODB_LOGDIR'] = os.path.join(os.path.sep, 'var', 'log', 'nuodb')
    os.environ['NUODB_RUNDIR'] = os.path.join(os.path.sep, 'var', 'run', 'nuodb')
    os.environ['NUODB_INSIGHTS_SERVICE_API'] = \
      'https://insights-dev.nuodb.com/api/1'
    insights.check_environment()
    file_path = insights.sub_filepath('testfile')
    self.assertTrue(file_path != None)

class TestShowInsights(unittest.TestCase):
  def runTest(self):
    # TODO
    pass

class TestCheckSubscriptionResponse(unittest.TestCase):
  def runTest(self):
    # TODO
    pass

class TestDeleteStoredSubscriptionInfo(unittest.TestCase):
  def runTest(self):
    # TODO
    pass

class TestStoreSubscriptionInfo(unittest.TestCase):
  def runTest(self):
    # TODO
    pass

class TestReadStoredSubscriptionInfo(unittest.TestCase):
  def runTest(self):
    # TODO
    pass

class TestGetSubscription(unittest.TestCase):
  def runTest(self):
    # TODO
    pass

class TestGetDomainConfigValue(unittest.TestCase):
  def runTest(self):
    # TODO
    pass

class TestGetDomainSubInfo(unittest.TestCase):
  def runTest(self):
    # TODO
    pass

class TestPostDomainConfigValue(unittest.TestCase):
  def runTest(self):
    # TODO
    pass

class TestStoreDomainSubInfo(unittest.TestCase):
  def runTest(self):
    # TODO
    pass

class TestClearDomainSubInfo(unittest.TestCase):
  def runTest(self):
    # TODO
    pass
