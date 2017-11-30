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

"""
Created on May 4, 2017

@author: tgates
"""
import os
import yaml


class NuocaConfig(object):
  """
  NuoCA Configuration elements.
  """
  NUOCA_TMPDIR = '/tmp/nuoca'  # Temporary directory for NuoCA
  NUOCA_LOGFILE = '/tmp/nuoca/nuoca.log'  # Path to logfile for NuoCA
  PLUGIN_PIPE_TIMEOUT = 5  # Plugin communication pipe timeout in seconds
  NUOCA_CONFIG_FILE = None
  SELFTEST_LOOP_COUNT = 5  # Number of Collection Intervals in selftest.
  SUBPROCESS_EXIT_TIMEOUT = 5  # Max seconds to wait for subprocess exit

  # Plugins that will be populated from the NuoCA configuration file.
  INPUT_PLUGINS = []
  OUTPUT_PLUGINS = []
  TRANSFORM_PLUGINS = []

  def _validate(self, userconfig):
    # TODO Implement
    pass

  def __init__(self, config_file):
    if not config_file:
      raise AttributeError("You must provide a NuoCA Config file")
    if not os.path.exists(config_file):
      raise AttributeError("Config file: %s does not exist" % config_file)
    userconfig = yaml.load(open(config_file).read())
    self._validate(userconfig)
    if not userconfig:
      return
    self.NUOCA_CONFIG_FILE = config_file
    for key, value in userconfig.iteritems():
      setattr(self, key, value)

