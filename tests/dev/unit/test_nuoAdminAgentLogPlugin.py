from __future__ import print_function

import os
import unittest
import nuoca_util
import time

from nuoca import NuoCA
from yapsy.MultiprocessPluginManager import MultiprocessPluginManager
from nuoca_plugin import NuocaMPInputPlugin, NuocaMPOutputPlugin, \
    NuocaMPTransformPlugin

from tests.dev.plugins.input.mpNuoAdminAgentLogPlugin import MPNuoAdminAgentLog


class TestInputPlugins(unittest.TestCase):
  def _MPNuoAdminAgentLogPluginTest(self):
    nuoca_util.initialize_logger("/tmp/nuoca.test.log")
    nuoAdminAgentLog_plugin = MPNuoAdminAgentLog(None)
    self.assertIsNotNone(nuoAdminAgentLog_plugin)
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

    cwd = os.getcwd()
    config = {'agentLogfile':
                "%s/../test_data/00f4e05b-403c-4f63-887e-c8331ef4087a"
                ".r0db0.agent.log" % cwd}
    plugin_msg = {'action': 'startup', 'config': config}
    plugin_resp_msg = None
    nuoAdminAgentLog_plugin.plugin_object.child_pipe.send(plugin_msg)
    if nuoAdminAgentLog_plugin.plugin_object.child_pipe.poll(child_pipe_timeout):
      plugin_resp_msg = nuoAdminAgentLog_plugin.plugin_object.child_pipe.recv()
    self.assertIsNotNone(plugin_resp_msg)
    self.assertEqual(0, plugin_resp_msg['status_code'])

    time.sleep(3)

    plugin_msg = {'action': 'collect', 'collection_interval': 3}
    plugin_resp_msg = None
    nuoAdminAgentLog_plugin.plugin_object.child_pipe.send(plugin_msg)
    if nuoAdminAgentLog_plugin.plugin_object.child_pipe.poll(child_pipe_timeout):
      plugin_resp_msg = nuoAdminAgentLog_plugin.plugin_object.child_pipe.recv()
    self.assertIsNotNone(plugin_resp_msg)
    resp_values = plugin_resp_msg['resp_values']
    self.assertIsNotNone(resp_values)
    self.assertEqual(0, plugin_resp_msg['status_code'])
    self.assertIsNotNone(resp_values['collected_values'])
    self.assertTrue(type(resp_values['collected_values']) is list)
    self.assertIsNotNone(resp_values['collected_values'][0]['nuoca_plugin'])
    self.assertIsNotNone(resp_values['collected_values'][0]['collect_timestamp'])

    plugin_msg = {'action': 'shutdown'}
    nuoAdminAgentLog_plugin.plugin_object.child_pipe.send(plugin_msg)

    plugin_msg = {'action': 'exit'}
    plugin_resp_msg = None
    nuoAdminAgentLog_plugin.plugin_object.child_pipe.send(plugin_msg)

    for a_plugin in all_plugins:
      self.manager.deactivatePluginByName(a_plugin.name, 'Input')
      self.assertFalse(a_plugin.is_activated)

  def runTest(self):
    topdir = nuoca_util.get_nuoca_topdir()
    input_plugin_dir = os.path.join(topdir, "tests/dev/plugins/input")
    dir_list = [input_plugin_dir]
    self._MPNuoAdminAgentLogPluginTest()
    self.manager = MultiprocessPluginManager(
        directories_list=dir_list,
        plugin_info_ext="multiprocess-plugin")
    self._MultiprocessPluginManagerTest()

  def tearDown(self):
    NuoCA.kill_all_plugin_processes(self.manager, timeout=1)


