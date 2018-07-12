# (C) Copyright NuoDB, Inc. 2017-2018
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.

from __future__ import print_function

import os
import unittest
import json


class TestForDomainOutput(unittest.TestCase):
    def runTest(self):
        self.assertTrue(os.path.isfile('/tmp/nuoca.nuodb_domain_tar.output.json'))


class TestDomainAuth(unittest.TestCase):
    def runTest(self):
        output = []
        with open('/tmp/nuoca.nuodb_domain_tar.output.json', 'r') as f:
            l = f.readline()

            while l:
                output.append(json.loads(l))
                l = f.readline()

        zbx_running = False
        nuo_admin_mon_running = False
        nuo_mon_running = False
        nuo_admin_agent_log_running = False

        for dict in output:
            for plugin in dict:
                if 'NuoCA.plugin_name' in plugin and plugin['NuoCA.plugin_name'] == 'ZBX':
                    self.assertIn('ZBX.system.uptime', plugin)
                    self.assertGreater(plugin['ZBX.system.uptime'], 0)
                    zbx_running = True
                if 'NuoCA.plugin_name' in plugin and plugin['NuoCA.plugin_name'] == 'NuoAdminMon':
                    self.assertIn('NuoAdminMon.TimeStamp', plugin)
                    self.assertGreater(plugin['NuoAdminMon.TimeStamp'], 0)
                    nuo_admin_mon_running = True
                if 'NuoCA.plugin_name' in plugin and plugin['NuoCA.plugin_name'] == 'NuoMon':
                    self.assertIn('NuoMon.NodeState', plugin)
                    self.assertEquals(plugin['NuoMon.NodeState'], 'Running')
                    nuo_mon_running = True
                if 'NuoCA.plugin_name' in plugin and plugin['NuoCA.plugin_name'] == 'NuoAdminAgentLog':
                    self.assertIn('NuoAdminAgentLog.path', plugin)
                    self.assertEquals(plugin['NuoAdminAgentLog.path'], '/var/log/nuodb/agent.log')
                    nuo_admin_agent_log_running = True

        # Verifying if all plugins are running correctly
        self.assertTrue(zbx_running)
        self.assertTrue(nuo_admin_mon_running)
        self.assertTrue(nuo_mon_running)
        self.assertTrue(nuo_admin_agent_log_running)

