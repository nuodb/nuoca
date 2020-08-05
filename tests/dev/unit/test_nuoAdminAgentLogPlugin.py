# (C) Copyright NuoDB, Inc. 2017-2018
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.

from __future__ import print_function

import os
import gzip
import unittest
from pynuoca import nuoca_util
import socket
import time
import json

from pynuoca.nuoca import NuoCA
from yapsy.MultiprocessPluginManager import MultiprocessPluginManager
from pynuoca.nuoca_plugin import NuocaMPInputPlugin, NuocaMPOutputPlugin, \
    NuocaMPTransformPlugin

from plugins.input.LogstashPlugin import LogstashPlugin

# List of key fields to compare.
compare_keys = [
  "action", "bhostname", "bindaddr", "bhost", "bindport", "comment",
  "dbname", "directory", "TimeStamp", "engine_pid", "entity", "exitcode",
  "iporaddr", "java_home", "java_runtime", "java_version", "java_vm",
  "logger", "loglevel", "message", "newnodeid", "description", "node_pid",
  "node_state", "node_type", "nodegroup", "nodeid", "nodeport", "peeraddr",
  "peertype", "port", "property", "propertyfile", "stableid", "startId",
  "thread", "value", "version"]

def hash_key_value(o):
  return o['hash']

# Make a list of dictionaries that contain all of the keys to compare
# and add a 'hash' of those key field values.
def values_to_compare(src_dict_list, compare_keys_list):
  ret_dict_list = list()
  for src_dict in src_dict_list:
    ret_dict = dict()
    for key in compare_keys_list:
      if key in src_dict:
        value = src_dict[key]
        if isinstance(value, (str, unicode)):
          ret_dict[key] = value.rstrip()
        else:
          ret_dict[key] = value
    ret_dict['hash'] = hash(frozenset(ret_dict.items()))
    ret_dict_list.append(ret_dict)
  ret_dict_list.sort(key=hash_key_value)
  return ret_dict_list

class TestInputPlugins(unittest.TestCase):
  def __init__(self, methodName='runTest'):
    self.manager = None
    self.local_hostname = socket.gethostname()
    self._nuoAdminAgentLog_plugin = None
    super(TestInputPlugins, self).__init__(methodName)

  def _LogstashPluginTest(self, test_node_id):
    logstash_plugin = None

    try:
      nuoca_util.initialize_logger("/tmp/nuoca.test.log")
      logstash_plugin = LogstashPlugin(None)
      self.assertIsNotNone(logstash_plugin)

      dir_path = os.path.dirname(os.path.realpath(__file__))
      config = {'logstashInputFilePath':
                  "%s/../test_data/%s.agent.log" % (dir_path, test_node_id),
                'logstashBin': os.path.expandvars('$LOGSTASH_HOME/bin/logstash'),
                'logstashConfig': os.path.expandvars('$NUOADMINAGENTLOGCONFIG'),
                'logstashSincedbPath': "/dev/null",
                'logstashOptions': '--pipeline.workers 1',
                'nuocaCollectionName': 'NuoAdminAgentLog',
                'host_uuid_shortname': True,
                'dropThrottledEvents': True}
      startup_rval = logstash_plugin.startup(config)
      self.assertTrue(startup_rval)
      time.sleep(90)
      resp_values = logstash_plugin.collect(3)
      self.assertIsNotNone(resp_values)
      self.assertTrue(type(resp_values) is list)
      self.assertTrue(len(resp_values) > 0)
      resp_values_compare = values_to_compare(resp_values, compare_keys)

      # To capture a new data.json file.
      #with open("%s.data.json" % test_node_id, 'w') as outfile:
      #  json.dump(resp_values, outfile)

      expected_json_file = "%s/../test_data/%s.expected.json.gz" % \
                           (dir_path, test_node_id)
      json_data = gzip.open(expected_json_file).read()
      expected_line_values = json.loads(json_data)
      expected_values_compare = values_to_compare(expected_line_values,
                                                  compare_keys)

      self.assertEqual(len(expected_values_compare),
                       len(resp_values_compare),
                       "Compare count of expected .vs. collected")

      counter = 0
      for expected_line in expected_values_compare:
        collected_line = resp_values_compare[counter]
        try:
          self.assertDictContainsSubset(expected_line,
                                        collected_line)
          counter += 1
        finally:
          pass

    finally:
      if logstash_plugin:
        logstash_plugin.shutdown()

  def _MultiprocessPluginManagerCompareTest(self):
    child_pipe_timeout = 600
    self.manager.setCategoriesFilter({
      "Input": NuocaMPInputPlugin,
      "Ouput": NuocaMPOutputPlugin,
      "Transform": NuocaMPTransformPlugin
    })

    try:
      self.manager.collectPlugins()
      all_plugins = self.manager.getAllPlugins()
      self.assertTrue(all_plugins)
      self.assertTrue(len(all_plugins) > 0)
      self._nuoAdminAgentLog_plugin = None
      for a_plugin in all_plugins:
        self.manager.activatePluginByName(a_plugin.name, 'Input')
        self.assertTrue(a_plugin.is_activated)
        if a_plugin.name == 'NuoAdminAgentLog':
          self._nuoAdminAgentLog_plugin = a_plugin
      self.assertIsNotNone(self._nuoAdminAgentLog_plugin)

      test_node_id = "00f4e05b-403c-4f63-887e-c8331ef4087a.r0db0"
      dir_path = os.path.dirname(os.path.realpath(__file__))
      config = {'logstashInputFilePath':
                  "%s/../test_data/%s.agent.log" % (dir_path, test_node_id),
                'logstashBin': os.path.expandvars('$LOGSTASH_HOME/bin/logstash'),
                'logstashConfig': os.path.expandvars('$NUOADMINAGENTLOGCONFIG'),
                'logstashSincedbPath': "/dev/null",
                'logstashOptions': '--pipeline.workers 1',
                'nuocaCollectionName': 'NuoAdminAgentLog'}
      plugin_msg = {'action': 'startup', 'config': config}
      plugin_resp_msg = None
      self._nuoAdminAgentLog_plugin.plugin_object.child_pipe.send(plugin_msg)
      if self._nuoAdminAgentLog_plugin.plugin_object.child_pipe. \
          poll(child_pipe_timeout):
        plugin_resp_msg = self._nuoAdminAgentLog_plugin.plugin_object.child_pipe.recv()
      self.assertIsNotNone(plugin_resp_msg)
      self.assertEqual(0, plugin_resp_msg['status_code'])

      time.sleep(90)

      plugin_msg = {'action': 'collect', 'collection_interval': 3}
      plugin_resp_msg = None
      self._nuoAdminAgentLog_plugin.plugin_object.child_pipe.send(plugin_msg)
      if self._nuoAdminAgentLog_plugin.plugin_object.child_pipe. \
          poll(child_pipe_timeout):
        plugin_resp_msg = self._nuoAdminAgentLog_plugin.plugin_object.child_pipe.recv()
      self.assertIsNotNone(plugin_resp_msg)
      resp_values = plugin_resp_msg['resp_values']
      self.assertIsNotNone(resp_values)
      self.assertEqual(0, plugin_resp_msg['status_code'])
      self.assertIsNotNone(resp_values['collected_values'])
      self.assertTrue(type(resp_values['collected_values']) is list)
      resp_values_compare = values_to_compare(resp_values['collected_values'], compare_keys)

      # To capture a new data.json file.
      #with open("%s.data.json" % test_node_id, 'w') as outfile:
      #  json.dump(resp_values, outfile)

      expected_json_file = "%s/../test_data/%s.expected.json.gz" % \
                           (dir_path, test_node_id)
      json_data = gzip.open(expected_json_file).read()
      expected_line_values = json.loads(json_data)

      expected_values_compare = values_to_compare(expected_line_values['collected_values'],
                                                  compare_keys)

      self.assertEqual(len(expected_values_compare),
                       len(resp_values_compare),
                       "Compare count of expected .vs. collected")

      counter = 0
      for expected_line in expected_values_compare:
        collected_line = resp_values_compare[counter]
        try:
          self.assertDictContainsSubset(expected_line,
                                        collected_line)
          counter += 1
        finally:
          pass

    finally:
      plugin_msg = {'action': 'shutdown'}
      self._nuoAdminAgentLog_plugin.plugin_object.child_pipe.send(plugin_msg)

      plugin_msg = {'action': 'exit'}
      self._nuoAdminAgentLog_plugin.plugin_object.child_pipe.send(plugin_msg)

      for a_plugin in all_plugins:
        self.manager.deactivatePluginByName(a_plugin.name, 'Input')
        self.assertFalse(a_plugin.is_activated)

  def runTest(self):
    topdir = nuoca_util.get_nuoca_topdir()
    input_plugin_dir = os.path.join(topdir, "plugins/input")
    dir_list = [input_plugin_dir]
    self._LogstashPluginTest(
      "06a32504-c2c9-41bc-9b48-030982c5ea43.r0db0")
    self._LogstashPluginTest(
      "fa2461c7-bca2-4df5-91e3-251084e1b8d1.r0db2")
    self.manager = MultiprocessPluginManager(
        directories_list=dir_list,
        plugin_info_ext="multiprocess-plugin")
    self._MultiprocessPluginManagerCompareTest()

  def tearDown(self):
    if self.manager:
      NuoCA.kill_all_plugin_processes(self.manager, timeout=10)
