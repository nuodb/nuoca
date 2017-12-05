# Copyright (c) 2017, NuoDB, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of NuoDB, Inc. nor the names of its contributors may
#       be used to endorse or promote products derived from this software
#       without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL NUODB, INC. BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA,
# OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
# ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from __future__ import print_function

import os
import unittest
import nuoca_util
from nuoca import NuoCA
from yapsy.MultiprocessPluginManager import MultiprocessPluginManager
from nuoca_plugin import NuocaMPInputPlugin, NuocaMPOutputPlugin, \
    NuocaMPTransformPlugin

from plugins.output.PrinterPlugin import PrinterPlugin


class TestOutputPlugins(unittest.TestCase):
  def _PrinterPluginTest(self):
    nuoca_util.initialize_logger("/tmp/nuoca.test.log")
    printer_plugin = PrinterPlugin(None)
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
      if a_plugin.name == 'Printer':
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
    output_plugin_dir = os.path.join(topdir, "plugins/output")
    dir_list = [output_plugin_dir]
    self._PrinterPluginTest()
    self.manager = MultiprocessPluginManager(
        directories_list=dir_list,
        plugin_info_ext="multiprocess-plugin")
    self._MultiprocessPluginManagerTest()

  def tearDown(self):
    NuoCA.kill_all_plugin_processes(self.manager, timeout=1)
