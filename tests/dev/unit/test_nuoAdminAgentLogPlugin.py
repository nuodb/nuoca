from __future__ import print_function

import os
import gzip
import unittest
import nuoca_util
import time
import json

from nuoca import NuoCA
from yapsy.MultiprocessPluginManager import MultiprocessPluginManager
from nuoca_plugin import NuocaMPInputPlugin, NuocaMPOutputPlugin, \
    NuocaMPTransformPlugin

from tests.dev.plugins.input.mpNuoAdminAgentLogPlugin import MPNuoAdminAgentLog


class TestInputPlugins(unittest.TestCase):
  def __init__(self, methodName='runTest'):
    self.manager = None
    super(TestInputPlugins, self).__init__(methodName)

  def _MPNuoAdminAgentLogPluginTest(self, test_node_id):
    nuoca_util.initialize_logger("/tmp/nuoca.test.log")
    nuoAdminAgentLog_plugin = MPNuoAdminAgentLog(None)
    self.assertIsNotNone(nuoAdminAgentLog_plugin)

    dir_path = os.path.dirname(os.path.realpath(__file__))
    config = {'agentLogfile':
              "%s/../test_data/%s.agent.log" % (dir_path, test_node_id),
              'host_uuid_shortname': True}
    startup_rval = nuoAdminAgentLog_plugin.startup(config)
    self.assertTrue(startup_rval)
    time.sleep(3)
    resp_values = nuoAdminAgentLog_plugin.collect(3)
    self.assertIsNotNone(resp_values)
    self.assertTrue(type(resp_values) is list)

    # To capture a new data.json file.
    # with open("%s.data.json" % test_node_id, 'w') as outfile:
    # json.dump(resp_values, outfile)

    expected_json_file = "%s/../test_data/%s.expected.json.gz" % \
                         (dir_path, test_node_id)
    json_data = gzip.open(expected_json_file).read()
    expected_line_values = json.loads(json_data)

    counter = 0
    for expected_line in expected_line_values:
      del expected_line['collect_timestamp']
      self.assertIsNotNone(resp_values[counter]['collect_timestamp'])
      self.assertDictContainsSubset(expected_line, resp_values[counter])
      counter += 1
    nuoAdminAgentLog_plugin.shutdown()

  def _MultiprocessPluginManagerTest(self):
    child_pipe_timeout = 600
    self.manager.setCategoriesFilter({
        "Input": NuocaMPInputPlugin,
        "Ouput": NuocaMPOutputPlugin,
        "Transform": NuocaMPTransformPlugin
    })

    self.manager.collectPlugins()
    all_plugins = self.manager.getAllPlugins()
    self.assertTrue(all_plugins)
    self.assertTrue(len(all_plugins) > 0)
    nuoAdminAgentLog_plugin = None
    for a_plugin in all_plugins:
      self.manager.activatePluginByName(a_plugin.name, 'Input')
      self.assertTrue(a_plugin.is_activated)
      if a_plugin.name == 'NuoAdminAgentLog':
        nuoAdminAgentLog_plugin = a_plugin
    self.assertIsNotNone(nuoAdminAgentLog_plugin)

    test_node_id = "00f4e05b-403c-4f63-887e-c8331ef4087a.r0db0"
    dir_path = os.path.dirname(os.path.realpath(__file__))
    config = {'agentLogfile':
              "%s/../test_data/%s.agent.log" % (dir_path, test_node_id)}
    plugin_msg = {'action': 'startup', 'config': config}
    plugin_resp_msg = None
    nuoAdminAgentLog_plugin.plugin_object.child_pipe.send(plugin_msg)
    if nuoAdminAgentLog_plugin.plugin_object.child_pipe.\
        poll(child_pipe_timeout):
      plugin_resp_msg = nuoAdminAgentLog_plugin.plugin_object.child_pipe.recv()
    self.assertIsNotNone(plugin_resp_msg)
    self.assertEqual(0, plugin_resp_msg['status_code'])

    time.sleep(5)

    plugin_msg = {'action': 'collect', 'collection_interval': 3}
    plugin_resp_msg = None
    nuoAdminAgentLog_plugin.plugin_object.child_pipe.send(plugin_msg)
    if nuoAdminAgentLog_plugin.plugin_object.child_pipe.\
        poll(child_pipe_timeout):
      plugin_resp_msg = nuoAdminAgentLog_plugin.plugin_object.child_pipe.recv()
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
    for expected_line in expected_line_values['collected_values']:
      del expected_line['collect_timestamp']
      self.assertIsNotNone(
        resp_values['collected_values'][counter]['collect_timestamp'])
      self.assertDictContainsSubset(expected_line,
                                    resp_values['collected_values'][counter])
      counter += 1

    plugin_msg = {'action': 'shutdown'}
    nuoAdminAgentLog_plugin.plugin_object.child_pipe.send(plugin_msg)

    plugin_msg = {'action': 'exit'}
    nuoAdminAgentLog_plugin.plugin_object.child_pipe.send(plugin_msg)

    for a_plugin in all_plugins:
      self.manager.deactivatePluginByName(a_plugin.name, 'Input')
      self.assertFalse(a_plugin.is_activated)

  def runTest(self):
    topdir = nuoca_util.get_nuoca_topdir()
    input_plugin_dir = os.path.join(topdir, "tests/dev/plugins/input")
    dir_list = [input_plugin_dir]
    self._MPNuoAdminAgentLogPluginTest(
      "06a32504-c2c9-41bc-9b48-030982c5ea43.r0db0")
    self._MPNuoAdminAgentLogPluginTest(
      "fa2461c7-bca2-4df5-91e3-251084e1b8d1.r0db2")
    self.manager = MultiprocessPluginManager(
        directories_list=dir_list,
        plugin_info_ext="multiprocess-plugin")
    self._MultiprocessPluginManagerTest()

  def tearDown(self):
    if self.manager:
      NuoCA.kill_all_plugin_processes(self.manager, timeout=10)


