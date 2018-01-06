# (C) Copyright NuoDB, Inc. 2017-2018
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.

from __future__ import print_function

import os
import unittest
import nuoca_util
import socket
import time

from nuoca import NuoCA
from yapsy.MultiprocessPluginManager import MultiprocessPluginManager
from nuoca_plugin import NuocaMPInputPlugin, NuocaMPOutputPlugin, \
    NuocaMPTransformPlugin

from plugins.input.NuoAdminMonitorPlugin import NuoAdminMonitorPlugin


class TestInputPlugins(unittest.TestCase):
  def __init__(self, methodName='runTest'):
    self.manager = None
    self.local_hostname = socket.gethostname()
    super(TestInputPlugins, self).__init__(methodName)

  def _validate_collection_response(self, response):
    required_fields = \
      [u'TimeStamp', u'admin.address', u'admin.hostname', u'admin.id',
       u'admin.ipaddress', u'admin.isBroker', u'admin.port', u'admin.stableId',
       u'admin.version', u'domainEnforcerEnabled', u'region',
       u'tag.archive_base', u'tag.cores', u'tag.cputype',
       u'tag.default_archive_base', u'tag.default_journal_base',
       u'tag.default_region', u'tag.journal_base', u'tag.os_num_cores',
       u'tag.os_num_cpu', u'tag.os_num_fs', u'tag.os_ram_mb', u'tag.ostype',
       u'tag.osversion', u'tag.region']
    for resp_item in response:
      for req_field in required_fields:
        self.assertTrue(req_field in resp_item)

  def _NuoAdminMonitorPluginTest(self):
    nuoca_util.initialize_logger("/tmp/nuoca.test.log")
    print("Testing NuoAdminMon with missing config file")
    nuoAdminMonitor_plugin = NuoAdminMonitorPlugin(None)
    self.assertIsNotNone(nuoAdminMonitor_plugin)
    empty_config = {}
    startup_rval = nuoAdminMonitor_plugin.startup(empty_config)
    self.assertFalse(startup_rval)
    expected_err_msg = "NuoAdminMon plugin: missing config file."
    self.assertEquals(expected_err_msg,
                      nuoca_util.nuoca_get_last_log_error_message())
    nuoAdminMonitor_plugin.shutdown()

    print("Testing NuoAdminMon with invalid admin_host config")
    nuoAdminMonitor_plugin = NuoAdminMonitorPlugin(None)
    self.assertIsNotNone(nuoAdminMonitor_plugin)
    start_ts = nuoca_util.nuoca_gettimestamp()
    config = {'admin_host': 'no-such-localhost',
              'domain_username': 'domain',
              'domain_password': 'bird',
              'nuoca_start_ts': start_ts}
    startup_rval = nuoAdminMonitor_plugin.startup(config)
    self.assertTrue(startup_rval)
    time.sleep(15)
    resp_values = nuoAdminMonitor_plugin.collect(3)
    expected_msg = "Max retries exceeded with url"
    for resp_item in resp_values:
      self.assertTrue('nuoca_collection_error' in resp_item)
      if 'nuoca_collection_error' in resp_item:
        self.assertTrue(expected_msg in resp_item['nuoca_collection_error'])
    nuoAdminMonitor_plugin.shutdown()

    print("Testing NuoAdminMon with invalid admin_rest_api_port config")
    nuoAdminMonitor_plugin = NuoAdminMonitorPlugin(None)
    self.assertIsNotNone(nuoAdminMonitor_plugin)
    start_ts = nuoca_util.nuoca_gettimestamp()
    config = {'admin_host': 'localhost',
              'admin_rest_api_port': 8901,
              'domain_username': 'domain',
              'domain_password': 'bird',
              'nuoca_start_ts': start_ts}
    startup_rval = nuoAdminMonitor_plugin.startup(config)
    self.assertTrue(startup_rval)
    time.sleep(13)
    resp_values = nuoAdminMonitor_plugin.collect(3)
    print(resp_values)
    expected_msg = "Max retries exceeded with url"
    for resp_item in resp_values:
      self.assertTrue('nuoca_collection_error' in resp_item)
      if 'nuoca_collection_error' in resp_item:
        self.assertTrue(expected_msg in resp_item['nuoca_collection_error'])
    nuoAdminMonitor_plugin.shutdown()

    print("Testing NuoAdminMon with invalid domain_password config")
    nuoAdminMonitor_plugin = NuoAdminMonitorPlugin(None)
    self.assertIsNotNone(nuoAdminMonitor_plugin)
    start_ts = nuoca_util.nuoca_gettimestamp()
    config = {'admin_host': 'localhost',
              'domain_username': 'domain',
              'domain_password': 'no-such-password',
              'nuoca_start_ts': start_ts}
    startup_rval = nuoAdminMonitor_plugin.startup(config)
    self.assertTrue(startup_rval)
    time.sleep(13)
    resp_values = nuoAdminMonitor_plugin.collect(3)
    print(resp_values)
    expected_msg = "NuoAdminMon: Error code '401' when calling Admin Rest API"
    for resp_item in resp_values:
      self.assertTrue('nuoca_collection_error' in resp_item)
      if 'nuoca_collection_error' in resp_item:
        self.assertTrue(expected_msg in resp_item['nuoca_collection_error'])
    nuoAdminMonitor_plugin.shutdown()

    print("Testing NuoAdminMon with a valid NuoDB config/instance")
    nuoAdminMonitor_plugin = NuoAdminMonitorPlugin(None)
    self.assertIsNotNone(nuoAdminMonitor_plugin)
    start_ts = nuoca_util.nuoca_gettimestamp()
    config = {'admin_host': 'localhost',
              'admin_rest_api_port': 8888,
              'domain_username': 'domain',
              'domain_password': 'bird',
              'host_uuid_shortname': True,
              'admin_collect_interval': 10,
              'admin_collect_timeout': 2,
              'nuoca_start_ts': start_ts}
    startup_rval = nuoAdminMonitor_plugin.startup(config)
    self.assertTrue(startup_rval)
    time.sleep(13)
    resp_values = nuoAdminMonitor_plugin.collect(3)
    self.assertIsNotNone(resp_values)
    self.assertTrue(isinstance(resp_values, list))
    self._validate_collection_response(resp_values)
    nuoAdminMonitor_plugin.shutdown()

  def _MultiprocessPluginManagerTest(self):
    child_pipe_timeout = 600
    self.manager.setCategoriesFilter({
        "Input": NuocaMPInputPlugin,
        "Ouput": NuocaMPOutputPlugin,
        "Transform": NuocaMPTransformPlugin
    })

    print("Testing NuoAdminMon with a NuoCA multi-process manager")
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
    start_ts = nuoca_util.nuoca_gettimestamp()
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
    time.sleep(13)
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
    self.assertTrue(resp_values['collected_values'], list)
    self._validate_collection_response(resp_values['collected_values'])

    plugin_msg = {'action': 'shutdown'}
    nuoAdminMonitor_plugin.plugin_object.child_pipe.send(plugin_msg)

    plugin_msg = {'action': 'exit'}
    nuoAdminMonitor_plugin.plugin_object.child_pipe.send(plugin_msg)

    for a_plugin in all_plugins:
      self.manager.deactivatePluginByName(a_plugin.name, 'Input')
      self.assertFalse(a_plugin.is_activated)

  def runTest(self):
    topdir = nuoca_util.get_nuoca_topdir()
    input_plugin_dir = os.path.join(topdir, "plugins/input")
    dir_list = [input_plugin_dir]
    self._NuoAdminMonitorPluginTest()
    self.manager = MultiprocessPluginManager(
        directories_list=dir_list,
        plugin_info_ext="multiprocess-plugin")
    self._MultiprocessPluginManagerTest()

  def tearDown(self):
    if self.manager:
      NuoCA.kill_all_plugin_processes(self.manager, timeout=10)
