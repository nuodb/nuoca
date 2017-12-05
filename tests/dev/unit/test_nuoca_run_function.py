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
import nuoca


class TestNuoCARunFunction(unittest.TestCase):

  def setUp(self):
    super(TestNuoCARunFunction, self).setUp()
    self._topdir = nuoca_util.get_nuoca_topdir()
    self._plugin_dir = os.path.join(self._topdir, "plugins")
    self._config_dir = os.path.join(self._topdir, "tests", "dev", "configs")

  def test_nuoca_function(self):
    self.assertTrue(os.path.isdir(self._topdir))
    self.assertTrue(os.path.isdir(self._plugin_dir))
    self.assertTrue(os.path.isdir(self._config_dir))
    nuoca.nuoca_run(
        config_file=os.path.join(self._config_dir, "counter_quick.yml"),
        collection_interval=1,
        log_level="ERROR",
        plugin_dir=self._plugin_dir,
        self_test=True,
        starttime=nuoca_util.nuoca_gettimestamp() + 3,
        verbose=False,
        output_values=None
    )
