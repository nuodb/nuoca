from __future__ import print_function

import os
import unittest
import nuoca_util
import json
from yapsy.MultiprocessPluginManager import MultiprocessPluginManager
from nuoca_plugin import NuocaMPInputPlugin, NuocaMPOutputPlugin, \
  NuocaMPTransformPlugin

from tests.dev.plugins.input.mpCounterPlugin import MPCounterPlugin
from tests.dev.plugins.output.mpPrinterPlugin import MPPrinterPlugin

class TestInputPlugins(unittest.TestCase):
  def _MPCounterPluginTest(self):
    counter_plugin = MPCounterPlugin(None)
    self.assertIsNotNone(counter_plugin)
    self.assertEqual(0, counter_plugin.get_count())
    counter_plugin.increment()
    self.assertEqual(1, counter_plugin.get_count())
    resp_values = counter_plugin.collect()
    self.assertIsNotNone(resp_values)
    self.assertIsNotNone(resp_values['nuoca_plugin'])
    self.assertEqual(2, resp_values['counter'])
    self.assertIsNotNone(resp_values['collect_timestamp'])

  def _MultiprocessPluginManagerTest(self, manager):
    child_pipe_timeout = 600
    self.manager = manager
    self.manager.setCategoriesFilter({
      "Input": NuocaMPInputPlugin,
      "Ouput": NuocaMPOutputPlugin,
      "Transform": NuocaMPTransformPlugin
    })

    self.manager.collectPlugins()
    all_plugins = self.manager.getAllPlugins()
    self.assertTrue(all_plugins)
    self.assertTrue(len(all_plugins) > 0)
    for a_plugin in all_plugins:
      self.manager.activatePluginByName(a_plugin.name, 'Input')
      self.assertTrue(a_plugin.is_activated)
      if a_plugin.name == 'mpCounterPlugin':
        counter_plugin = a_plugin
    self.assertIsNotNone(counter_plugin)

    plugin_msg = "collect"
    plugin_resp_msg = None
    counter_plugin.plugin_object.child_pipe.send(plugin_msg)
    if counter_plugin.plugin_object.child_pipe.poll(child_pipe_timeout):
      plugin_resp_msg = counter_plugin.plugin_object.child_pipe.recv()
    self.assertIsNotNone(plugin_resp_msg)
    resp_values = json.loads(plugin_resp_msg)
    self.assertIsNotNone(resp_values)
    self.assertEqual(0, resp_values['status_code'])
    self.assertIsNotNone(resp_values['collected_values'])
    self.assertIsNotNone(resp_values['collected_values']['nuoca_plugin'])
    self.assertEqual(1, resp_values['collected_values']['counter'])
    self.assertIsNotNone(resp_values['collected_values']['collect_timestamp'])

    plugin_msg = "exit"
    plugin_resp_msg = None
    counter_plugin.plugin_object.child_pipe.send(plugin_msg)
    if counter_plugin.plugin_object.child_pipe.poll(child_pipe_timeout):
      plugin_resp_msg = counter_plugin.plugin_object.child_pipe.recv()
    self.assertIsNotNone(plugin_resp_msg)

    for a_plugin in all_plugins:
      self.manager.deactivatePluginByName(a_plugin.name, 'Input')
      self.assertFalse(a_plugin.is_activated)

  def runTest(self):
    topdir = nuoca_util.get_nuoca_topdir()
    input_plugin_dir = os.path.join(topdir, "tests/dev/plugins/input")
    dir_list = [input_plugin_dir]
    self._MPCounterPluginTest()
    manager = MultiprocessPluginManager(directories_list=dir_list,
                                        plugin_info_ext="multiprocess-plugin")
    self._MultiprocessPluginManagerTest(manager)


