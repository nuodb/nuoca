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

from tests.dev.plugins.input.NuoAdminMonitorPlugin import NuoAdminMonitor


class TestInputPlugins(unittest.TestCase):
  def __init__(self, methodName='runTest'):
    self.manager = None
    self.local_hostname = socket.gethostname()
    super(TestInputPlugins, self).__init__(methodName)

  def _NuoAdminMonitorPluginTest(self):
    nuoca_util.initialize_logger("/tmp/nuoca.test.log")
    nuoAdminMonitor_plugin = NuoAdminMonitor(None)
    self.assertIsNotNone(nuoAdminMonitor_plugin)
    config = {'admin_host': 'localhost',
              'domain_username': 'domain',
              'domain_password': 'bird',
              'host_uuid_shortname': True}
    startup_rval = nuoAdminMonitor_plugin.startup(config)
    self.assertTrue(startup_rval)
    time.sleep(3)
    resp_values = nuoAdminMonitor_plugin.collect(3)
    self.assertIsNotNone(resp_values)
    self.assertTrue(type(resp_values) is list)
    nuoAdminMonitor_plugin.shutdown()

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
    nuoAdminMonitor_plugin = None
    for a_plugin in all_plugins:
      self.manager.activatePluginByName(a_plugin.name, 'Input')
      self.assertTrue(a_plugin.is_activated)
      if a_plugin.name == 'NuoAdminMon':
        nuoAdminMonitor_plugin = a_plugin
    self.assertIsNotNone(nuoAdminMonitor_plugin)
    config = {'admin_host': 'localhost',
              'domain_username': 'domain',
              'domain_password': 'bird',
              'host_uuid_shortname': True}
    plugin_msg = {'action': 'startup', 'config': config}
    plugin_resp_msg = None
    nuoAdminMonitor_plugin.plugin_object.child_pipe.send(plugin_msg)
    if nuoAdminMonitor_plugin.plugin_object.child_pipe.\
        poll(child_pipe_timeout):
      plugin_resp_msg = nuoAdminMonitor_plugin.plugin_object.child_pipe.recv()
    self.assertIsNotNone(plugin_resp_msg)
    self.assertEqual(0, plugin_resp_msg['status_code'])
    time.sleep(5)
    plugin_msg = {'action': 'collect', 'collection_interval': 3}
    plugin_resp_msg = None
    nuoAdminMonitor_plugin.plugin_object.child_pipe.send(plugin_msg)
    if nuoAdminMonitor_plugin.plugin_object.child_pipe.\
        poll(child_pipe_timeout):
      plugin_resp_msg = nuoAdminMonitor_plugin.plugin_object.child_pipe.recv()
    self.assertIsNotNone(plugin_resp_msg)
    resp_values = plugin_resp_msg['resp_values']
    self.assertIsNotNone(resp_values)
    self.assertEqual(0, plugin_resp_msg['status_code'])
    self.assertIsNotNone(resp_values['collected_values'])
    self.assertTrue(type(resp_values['collected_values']) is list)


    plugin_msg = {'action': 'shutdown'}
    nuoAdminMonitor_plugin.plugin_object.child_pipe.send(plugin_msg)

    plugin_msg = {'action': 'exit'}
    nuoAdminMonitor_plugin.plugin_object.child_pipe.send(plugin_msg)

    for a_plugin in all_plugins:
      self.manager.deactivatePluginByName(a_plugin.name, 'Input')
      self.assertFalse(a_plugin.is_activated)

  def runTest(self):
    topdir = nuoca_util.get_nuoca_topdir()
    input_plugin_dir = os.path.join(topdir, "tests/dev/plugins/input")
    dir_list = [input_plugin_dir]
    self._NuoAdminMonitorPluginTest()
    self.manager = MultiprocessPluginManager(
        directories_list=dir_list,
        plugin_info_ext="multiprocess-plugin")
    self._MultiprocessPluginManagerTest()

  def tearDown(self):
    if self.manager:
      NuoCA.kill_all_plugin_processes(self.manager, timeout=10)


