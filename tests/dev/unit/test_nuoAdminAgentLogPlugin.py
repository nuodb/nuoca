from __future__ import print_function

import os
import gzip
import unittest
import nuoca_util
import socket
import time
import json

from nuoca import NuoCA
from yapsy.MultiprocessPluginManager import MultiprocessPluginManager
from nuoca_plugin import NuocaMPInputPlugin, NuocaMPOutputPlugin, \
    NuocaMPTransformPlugin

from plugins.input.LogstashPlugin import LogstashPlugin


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
                'host_uuid_shortname': True}
      startup_rval = logstash_plugin.startup(config)
      self.assertTrue(startup_rval)
      time.sleep(30)
      resp_values = logstash_plugin.collect(3)
      self.assertIsNotNone(resp_values)
      self.assertTrue(type(resp_values) is list)
      self.assertTrue(len(resp_values) > 0)

      # To capture a new data.json file.
      # with open("%s.data.json" % test_node_id, 'w') as outfile:
      #   json.dump(resp_values, outfile)

      expected_json_file = "%s/../test_data/%s.expected.json.gz" % \
                           (dir_path, test_node_id)
      json_data = gzip.open(expected_json_file).read()
      expected_line_values = json.loads(json_data)

      counter = 0
      for expected_line in expected_line_values:
        del expected_line['collect_timestamp']
        del expected_line['@timestamp']
        if 'tags' in expected_line:
          del expected_line['tags']
        collected_line = resp_values[counter]
        if 'tags' in collected_line:
          del collected_line['tags']
        try:
          expected_line['Hostname'] = self.local_hostname
          expected_line['host'] = self.local_hostname
          expected_line['nuoca_plugin'] = 'Logstash'
          if '@timestamp' in collected_line:
            del collected_line['@timestamp']
          self.assertIsNotNone(collected_line['collect_timestamp'])
          if 'comment' in expected_line:
            if isinstance(expected_line['comment'], basestring):
              expected_line['comment'] = expected_line['comment'].rstrip()
          if 'message' in expected_line:
            if isinstance(expected_line['message'], basestring):
              expected_line['message'] = expected_line['message'].rstrip()
          s1 = False
          try:
            s1 = set(expected_line.items()).issubset(
              set(collected_line.items()))
          except Exception as e:
            print(str(e))
          if not s1:
            pass
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

      time.sleep(30)

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

      # To capture a new data.json file.
      # with open("%s.data.json" % test_node_id, 'w') as outfile:
      #   json.dump(resp_values, outfile)

      expected_json_file = "%s/../test_data/%s.expected.json.gz" % \
                           (dir_path, test_node_id)
      json_data = gzip.open(expected_json_file).read()
      expected_line_values = json.loads(json_data)

      counter = 0
      resp_collected_values = resp_values['collected_values']
      for expected_line in expected_line_values['collected_values']:
        # print("counter: %s" % str(counter))
        collected_line = resp_collected_values[counter]
        try:
          del expected_line['@timestamp']
          del collected_line['@timestamp']
          del expected_line['collect_timestamp']
          expected_line['Hostname'] = self.local_hostname
          expected_line['host'] = self.local_hostname
          #          if 'value' in expected_line:  # TEMP
          #            if expected_line['value'] == '':
          #              del expected_line['value']
          if 'tags' in collected_line:
            del collected_line['tags']
          if 'tags' in expected_line:
            del expected_line['tags']
          self.assertIsNotNone(
            collected_line['collect_timestamp'])
          if 'comment' in expected_line:
            if isinstance(expected_line['comment'], basestring):
              expected_line['comment'] = expected_line['comment'].rstrip()
          if 'message' in expected_line:
            if isinstance(expected_line['message'], basestring):
              expected_line['message'] = expected_line['message'].rstrip()
          s1 = False
          try:
            s1 = set(expected_line.items()).issubset(
              set(collected_line.items()))
          except Exception as e:
            print(str(e))
          if not s1:
            pass
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
