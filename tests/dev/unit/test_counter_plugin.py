from __future__ import print_function

import os
import unittest
import nuoca_util
from nuoca import NuoCA
from yapsy.MultiprocessPluginManager import MultiprocessPluginManager
from nuoca_plugin import NuocaMPInputPlugin, NuocaMPOutputPlugin, \
    NuocaMPTransformPlugin

from tests.dev.plugins.input.mpCounterPlugin import MPCounterPlugin


class TestInputPlugins(unittest.TestCase):
  def _MPCounterPluginTest(self):
    counter_plugin = MPCounterPlugin(None)
    self.assertIsNotNone(counter_plugin)
    config = {'increment': 'not-an-integer'}
    startup_rval = counter_plugin.startup(config)
    self.assertFalse(startup_rval)
    config = {'increment': 1}
    startup_rval = counter_plugin.startup(config)
    self.assertTrue(startup_rval)
    self.assertEqual(0, counter_plugin.get_count())
    counter_plugin.increment()
    self.assertEqual(1, counter_plugin.get_count())
    resp_values = counter_plugin.collect(3)
    self.assertIsNotNone(resp_values)
    self.assertTrue(type(resp_values) is list)
    self.assertIsNotNone(resp_values[0]['nuoca_plugin'])
    self.assertEqual(2, resp_values[0]['counter'])
    self.assertIsNotNone(resp_values[0]['collect_timestamp'])
    counter_plugin.shutdown()

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
    counter_plugin = None
    for a_plugin in all_plugins:
      self.manager.activatePluginByName(a_plugin.name, 'Input')
      self.assertTrue(a_plugin.is_activated)
      if a_plugin.name == 'Counter':
        counter_plugin = a_plugin
    self.assertIsNotNone(counter_plugin)

    plugin_msg = {'action': 'startup', 'config': None}
    plugin_resp_msg = None
    counter_plugin.plugin_object.child_pipe.send(plugin_msg)
    if counter_plugin.plugin_object.child_pipe.poll(child_pipe_timeout):
      plugin_resp_msg = counter_plugin.plugin_object.child_pipe.recv()
    self.assertIsNotNone(plugin_resp_msg)
    self.assertEqual(0, plugin_resp_msg['status_code'])

    plugin_msg = {'action': 'collect', 'collection_interval': 3}
    plugin_resp_msg = None
    counter_plugin.plugin_object.child_pipe.send(plugin_msg)
    if counter_plugin.plugin_object.child_pipe.poll(child_pipe_timeout):
      plugin_resp_msg = counter_plugin.plugin_object.child_pipe.recv()
    self.assertIsNotNone(plugin_resp_msg)
    resp_values = plugin_resp_msg['resp_values']
    self.assertIsNotNone(resp_values)
    self.assertEqual(0, plugin_resp_msg['status_code'])
    self.assertIsNotNone(resp_values['collected_values'])
    self.assertTrue(type(resp_values['collected_values']) is list)
    self.assertIsNotNone(resp_values['collected_values'][0]['nuoca_plugin'])
    self.assertEqual(1, resp_values['collected_values'][0]['counter'])
    self.assertIsNotNone(resp_values['collected_values'][0]['collect_timestamp'])

    plugin_msg = {'action': 'shutdown'}
    counter_plugin.plugin_object.child_pipe.send(plugin_msg)

    plugin_msg = {'action': 'exit'}
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
    self.manager = MultiprocessPluginManager(
        directories_list=dir_list,
        plugin_info_ext="multiprocess-plugin")
    self._MultiprocessPluginManagerTest()

  def tearDown(self):
    NuoCA.kill_all_plugin_processes(self.manager, timeout=1)


