from __future__ import print_function

import os
import unittest
import nuoca_util
from nuoca import NuoCA
from yapsy.MultiprocessPluginManager import MultiprocessPluginManager
from nuoca_plugin import NuocaMPInputPlugin, NuocaMPOutputPlugin, \
    NuocaMPTransformPlugin

from tests.dev.plugins.output.mpPrinterPlugin import MPPrinterPlugin


class TestOutputPlugins(unittest.TestCase):
  def _MPPrinterPluginTest(self):
    printer_plugin = MPPrinterPlugin(None)
    self.assertIsNotNone(printer_plugin)
    startup_rval = printer_plugin.startup(None)
    self.assertTrue(startup_rval)
    printer_plugin.store({'message': 'hello'})

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
    printer_plugin = None
    for a_plugin in all_plugins:
      self.manager.activatePluginByName(a_plugin.name, 'Output')
      if a_plugin.name == 'mpPrinterPlugin':
        printer_plugin = a_plugin
    self.assertIsNotNone(printer_plugin)

    plugin_msg = {'action': 'startup', 'config': None}
    plugin_resp_msg = None
    printer_plugin.plugin_object.child_pipe.send(plugin_msg)
    if printer_plugin.plugin_object.child_pipe.poll(child_pipe_timeout):
      plugin_resp_msg = printer_plugin.plugin_object.child_pipe.recv()
    self.assertIsNotNone(plugin_resp_msg)
    self.assertEqual(0, plugin_resp_msg['status_code'])

    store_data = {'foo': 1, 'bar': 2}
    plugin_msg = {'action': "store", 'ts_values': store_data}
    plugin_resp_msg = None
    printer_plugin.plugin_object.child_pipe.send(plugin_msg)
    if printer_plugin.plugin_object.child_pipe.poll(child_pipe_timeout):
      plugin_resp_msg = printer_plugin.plugin_object.child_pipe.recv()
    self.assertIsNotNone(plugin_resp_msg)
    self.assertTrue('status_code' in plugin_resp_msg)
    self.assertEqual(0, plugin_resp_msg['status_code'])

    plugin_msg = {'action': "exit"}
    plugin_resp_msg = None
    printer_plugin.plugin_object.child_pipe.send(plugin_msg)
    if printer_plugin.plugin_object.child_pipe.poll(child_pipe_timeout):
      plugin_resp_msg = printer_plugin.plugin_object.child_pipe.recv()
    self.assertIsNotNone(plugin_resp_msg)

    for a_plugin in all_plugins:
      self.manager.deactivatePluginByName(a_plugin.name, 'Output')
      self.assertFalse(a_plugin.is_activated)

  def runTest(self):
    topdir = nuoca_util.get_nuoca_topdir()
    output_plugin_dir = os.path.join(topdir, "tests/dev/plugins/output")
    dir_list = [output_plugin_dir]
    self._MPPrinterPluginTest()
    self.manager = MultiprocessPluginManager(
        directories_list=dir_list,
        plugin_info_ext="multiprocess-plugin")
    self._MultiprocessPluginManagerTest()

  def tearDown(self):
    NuoCA.kill_all_plugin_processes(self.manager, timeout=1)
