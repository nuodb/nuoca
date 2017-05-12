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
  VAGRANT_TESTHOST = '192.168.60.10'  # Used for internal testing
  VAGRANT_USER = 'vagrant'  # Used for internal testing
  PLUGIN_PIPE_TIMEOUT = 5  # Plugin communication pipe timeout in seconds
  NUOCA_CONFIG_FILE = None

  # Plugins that will be populated from the NuoCA configuration file.
  INPUT_PLUGINS = []
  OUTPUT_PLUGINS = []
  TRANSFORM_PLUGINS = []

  def __init__(self, config_file):
    if not config_file:
      raise AttributeError("You must provide a NuoCA Config file")
    if not os.path.exists(config_file):
      raise AttributeError("Config file: %s does not exist" % config_file)
    userconfig = yaml.load(open(config_file).read())
    if not userconfig:
      return
    self.NUOCA_CONFIG_FILE = config_file
    for key, value in userconfig.iteritems():
      setattr(self, key, value)

