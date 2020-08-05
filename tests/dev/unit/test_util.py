# (C) Copyright NuoDB, Inc. 2017-2018
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.

from __future__ import print_function

import datetime
import os
import sys
import time
import unittest
from pynuoca import nuoca_util
import logging
import socket

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
    nuoca_util.initialize_logger("/tmp/nuoca.test.log")
    nuoca_util.nuoca_set_log_level(logging.INFO)
    info_message = "Info message"
    nuoca_util.nuoca_log(logging.INFO, info_message)
    self.assertEquals(info_message, nuoca_util.nuoca_get_last_log_message())
    error_message = "Error message"
    nuoca_util.nuoca_log(logging.ERROR, error_message)
    self.assertEquals(error_message,
                      nuoca_util.nuoca_get_last_log_error_message())
    nuoca_util.nuoca_logging_shutdown()


class TestUtilParseOptions(unittest.TestCase):
  def test_none_returns_empty_dict(self):
    # suppress PEP-8 warning in pycharm - deliberate wrong type for test
    # noinspection PyTypeChecker
    m = nuoca_util.parse_keyval_list(None)
    self.assertDictEqual(m, {})

  def test_empty_list_returns_empty_dict(self):
    m = nuoca_util.parse_keyval_list([])
    self.assertDictEqual(m, {})

  def test_empty_strings_ignored(self):
    m = nuoca_util.parse_keyval_list(['', '  ', ',', '  ,  ,  ,  ,'])
    self.assertDictEqual(m, {})

  def test_parse_basic_single(self):
    options = ['a=my-value']
    act = nuoca_util.parse_keyval_list(options)
    exp = {'a': 'my-value'}
    self.assertItemsEqual(act, exp)

  def test_parse_basic_several(self):
    options = ['a=b', 'b=c', 'c=d', "e=f"]
    act = nuoca_util.parse_keyval_list(options)
    exp = {'a': 'b', 'b': 'c', 'c': 'd', 'e': 'f'}
    self.assertItemsEqual(act, exp)

  def test_multi_element(self):
    options = ['a=1,b=2', 'd=4']
    act = nuoca_util.parse_keyval_list(options)
    exp = {'a': '1', 'b': '2', 'd': '4'}
    self.assertItemsEqual(act, exp)

  def test_elements_are_trimmed_for_convenience(self):
    options = [' a = my-value ']
    act = nuoca_util.parse_keyval_list(options)
    exp = {'a': 'my-value'}
    self.assertItemsEqual(act, exp)

  def test_even_multi_elements_are_trimmed(self):
    options = [
      ' a = peanut  , b = butter,  '
      'c =  but spaces  in the   middle are kept   ']
    act = nuoca_util.parse_keyval_list(options)
    exp = {'a': 'peanut',
           'b': 'butter',
           'c': 'but spaces  in the   middle are kept'}
    self.assertItemsEqual(act, exp)

  def test_same_key_listed_twice(self):
    # second wins
    options = ['a=1', 'd=4', 'a=antelope']
    act = nuoca_util.parse_keyval_list(options)
    exp = {'a': 'antelope', 'd': '4'}
    self.assertItemsEqual(act, exp)

  def test_value_anything_but_comma_equal_allowed_but_dangerous(self):
    options = ['a= an elephant, b=and a --large-- ant',
               'c=walk into a !@#$%^&*() bar']
    act = nuoca_util.parse_keyval_list(options)
    exp = {'a': ' an elephant', 'b': 'and a --large-- ant',
           'c': 'walk into a !@#$%^&*() bar'}
    self.assertItemsEqual(act, exp)

  def test_single_bad(self):
    with self.assertRaisesRegexp(AttributeError,
                                 "key/value pair bananans missing '='"):
      nuoca_util.parse_keyval_list(['bananans'])

  def test_neg_options_multi_bad(self):
    with self.assertRaisesRegexp(AttributeError,
                                 "key/value pair crunch missing '='"):
      nuoca_util.parse_keyval_list(['apple=jacks,crunch'])

class TestProcessRunning(unittest.TestCase):
  def runTest(self):
    p1_status = nuoca_util.search_running_processes('python')
    self.assertTrue(p1_status)
    p2_status = nuoca_util.search_running_processes('no-such-process')
    self.assertFalse(p2_status)


class TestExecuteCommand(unittest.TestCase):
  def runTest(self):
    (ec, stdout, stderr) = nuoca_util.execute_command('hostname')
    self.assertEqual(0, ec)
    localhostname = socket.gethostname()
    self.assertEqual(localhostname, stdout.strip())
    self.assertEqual('', stderr)
    (ec, stdout, stderr) = nuoca_util.execute_command('no-such-command')
    self.assertEqual(127, ec)
    self.assertEqual('', stdout)
    self.assertTrue('no-such-command: not found' in stderr)


class TestCoerceNumeric(unittest.TestCase):
  def runTest(self):
    val1 = nuoca_util.coerce_numeric('23')
    self.assertTrue(type(val1) is int)
    self.assertEqual(23, val1)
    val2 = nuoca_util.coerce_numeric('3.141597')
    self.assertTrue(type(val2) is float)
    self.assertEqual(3.141597, val2)
    val3 = nuoca_util.coerce_numeric('foo')
    self.assertTrue(type(val3) is str)
    self.assertEqual('foo', val3)


class TestIntervalSync1(unittest.TestCase):
  def runTest(self):
    utc_tzinfo = nuoca_util.UTC()
    is1 = nuoca_util.IntervalSync(interval=3)
    now_dt = datetime.datetime.now(utc_tzinfo)
    interval_ts1 = is1.compute_next_interval()
    self.assertGreaterEqual(interval_ts1, now_dt)
    ts1_diff = interval_ts1 - now_dt
    ts1_seconds = ts1_diff.total_seconds()
    self.assertLessEqual(ts1_seconds, 6.0)
    ts2 = is1.wait_for_next_interval()
    ts3 = is1.wait_for_next_interval()
    ts2_diff = ts3 - ts2
    self.assertEqual(ts2_diff, 3)

class TestIntervalSync2(unittest.TestCase):
  def runTest(self):
    utc_tzinfo = nuoca_util.UTC()
    seed_ts1 = int(time.time()) - 1 # start in the past
    is1 = nuoca_util.IntervalSync(interval=3, seed_ts=seed_ts1)
    now_dt = datetime.datetime.now(utc_tzinfo)
    interval_ts1 = is1.compute_next_interval()
    self.assertGreaterEqual(interval_ts1, now_dt)
    ts1_diff = interval_ts1 - now_dt
    ts1_seconds = ts1_diff.total_seconds()
    self.assertLessEqual(ts1_seconds, 6.0)
    ts1_epoch_seconds = \
      (interval_ts1 -
       datetime.datetime(1970, 1, 1, tzinfo=utc_tzinfo)).total_seconds()
    self.assertEqual(ts1_epoch_seconds, seed_ts1+3)

class TestIntervalSync3(unittest.TestCase):
  def runTest(self):
    utc_tzinfo = nuoca_util.UTC()
    seed_ts1 = int(time.time()) + 10 # start in the future
    is1 = nuoca_util.IntervalSync(interval=3, seed_ts=seed_ts1)
    now_dt = datetime.datetime.now(utc_tzinfo)
    interval_ts1 = is1.compute_next_interval()
    self.assertGreaterEqual(interval_ts1, now_dt)
    ts1_diff = interval_ts1 - now_dt
    ts1_seconds = ts1_diff.total_seconds()
    self.assertAlmostEqual(ts1_seconds, 10.0, delta=0.1)
    ts1_epoch_seconds = \
      (interval_ts1 -
       datetime.datetime(1970, 1, 1, tzinfo=utc_tzinfo)).total_seconds()
    self.assertEqual(ts1_epoch_seconds, seed_ts1)

class TestToBool(unittest.TestCase):
  def runTest(self):
    # Test cases
    assert nuoca_util.to_bool('true'), '"true" is True'
    assert nuoca_util.to_bool('True'), '"True" is True'
    assert nuoca_util.to_bool('TRue'), '"TRue" is True'
    assert nuoca_util.to_bool('TRUE'), '"TRUE" is True'
    assert nuoca_util.to_bool('T'), '"T" is True'
    assert nuoca_util.to_bool('t'), '"t" is True'
    assert nuoca_util.to_bool('1'), '"1" is True'
    assert nuoca_util.to_bool(True), 'True is True'
    assert nuoca_util.to_bool(u'true'), 'unicode "true" is True'

    assert nuoca_util.to_bool('false') is False, '"false" is False'
    assert nuoca_util.to_bool('False') is False, '"False" is False'
    assert nuoca_util.to_bool('FAlse') is False, '"FAlse" is False'
    assert nuoca_util.to_bool('FALSE') is False, '"FALSE" is False'
    assert nuoca_util.to_bool('F') is False, '"F" is False'
    assert nuoca_util.to_bool('f') is False, '"f" is False'
    assert nuoca_util.to_bool('0') is False, '"0" is False'
    assert nuoca_util.to_bool(False) is False, 'False is False'
    assert nuoca_util.to_bool(u'false') is False, 'unicode "false" is False'

    # Expect ValueError to be raised for invalid parameter...
    try:
      nuoca_util.to_bool('')
      nuoca_util.to_bool(12)
      nuoca_util.to_bool([])
      nuoca_util.to_bool('yes')
      nuoca_util.to_bool('FOObar')
    except ValueError, e:
      pass

if __name__ == '__main__':
  sys.exit(unittest.main())
