# (C) Copyright NuoDB, Inc. 2017-2018
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.

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
  NUOCA_COLLECTION_INTERVAL = None  # Override NuoCA Collection Interval

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

