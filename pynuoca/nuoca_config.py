# (C) Copyright NuoDB, Inc. 2017-2020
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.

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

    # Check each Input plugin configuration for 'NuoCA.route'. If found
    # check it against each Output plugin, and remove any routes
    # that don't match an actual Output plugin.  Essentially rewriting
    # each 'NuoCA.route' configuration to match actual routes.
    def _adjust_route(self, userconfig):
        if not userconfig:
            return
        if 'INPUT_PLUGINS' in userconfig:
            for input_plugin in userconfig['INPUT_PLUGINS']:
                input_plugin_name = input_plugin.keys()[0]
                input_plugin_config = input_plugin.values()[0]
                try:
                    if 'NuoCA.route' in input_plugin_config:
                        self.is_routing = True
                        actual_route_list = []
                        candidate_route_list = \
                            input_plugin_config['NuoCA.route'].split(',')
                        for candidate_route in candidate_route_list:
                            for output_plugin in userconfig['OUTPUT_PLUGINS']:
                                output_plugin_name = output_plugin.keys()[0]
                                if candidate_route == output_plugin_name:
                                    actual_route_list.append(output_plugin_name)
                        input_plugin_config['NuoCA.route'] = ','.join(actual_route_list)
                except:
                    pass

    def __init__(self, config_file):
        self.is_routing = False
        if not config_file:
            raise AttributeError("You must provide a NuoCA Config file")
        if not os.path.exists(config_file):
            raise AttributeError("Config file: %s does not exist" % config_file)
        userconfig = yaml.safe_load(open(config_file).read())
        self._validate(userconfig)
        self._adjust_route(userconfig)
        if not userconfig:
            return
        self.NUOCA_CONFIG_FILE = config_file
        for key, value in userconfig.iteritems():
            setattr(self, key, value)
