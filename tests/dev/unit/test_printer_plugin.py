from __future__ import print_function

import os
import unittest
import nuoca_util
import json
from yapsy.MultiprocessPluginManager import MultiprocessPluginManager
from nuoca_plugin import NuocaMPInputPlugin, NuocaMPOutputPlugin, \
  NuocaMPTransformPlugin

from tests.dev.plugins.output.mpPrinterPlugin import MPPrinterPlugin

class TestOutputPlugins(unittest.TestCase):
  def _MPPrinterPluginTest(self):
    printer_plugin = MPPrinterPlugin(None)
    self.assertIsNotNone(printer_plugin)
    printer_plugin.store({'message': 'hello'})

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
      self.manager.activatePluginByName(a_plugin.name, 'Output')
      if a_plugin.name == 'mpPrinterPlugin':
        printer_plugin = a_plugin
    self.assertIsNotNone(printer_plugin)


    store_data = {'Action': "Store",
                  'TS_Values' : {
                    'foo' : 1,
                    'bar' : 2
                  }
                 }
    plugin_msg = json.dumps(store_data)
    plugin_resp_msg = None
    printer_plugin.plugin_object.child_pipe.send(plugin_msg)
    if printer_plugin.plugin_object.child_pipe.poll(child_pipe_timeout):
      plugin_resp_msg = printer_plugin.plugin_object.child_pipe.recv()
    self.assertIsNotNone(plugin_resp_msg)
    resp_values = json.loads(plugin_resp_msg)
    self.assertIsNotNone(resp_values)
    self.assertTrue('StatusCode' in resp_values)
    self.assertEqual(0, resp_values['StatusCode'])

    plugin_msg = '{"Action": "Exit"}'
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
    manager = MultiprocessPluginManager(directories_list=dir_list,
                                        plugin_info_ext="multiprocess-plugin")
    self._MultiprocessPluginManagerTest(manager)

