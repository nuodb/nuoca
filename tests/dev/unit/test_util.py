from __future__ import print_function

import os
import sys
import unittest
import nuoca_util
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
    nuoca_util.nuoca_log(logging.INFO, "Info message")
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
      ' a = peanut  , b = butter,  c =  but spaces  in the   middle are kept   ']
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

if __name__ == '__main__':
  sys.exit(unittest.main())
