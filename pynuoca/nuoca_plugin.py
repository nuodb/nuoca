# (C) Copyright NuoDB, Inc. 2017-2020
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.

import os
import traceback
import logging
from pynuoca.nuoca_util import nuoca_gettimestamp, nuoca_log
from yapsy.IMultiprocessChildPlugin import IMultiprocessChildPlugin


class NuocaMPPlugin(IMultiprocessChildPlugin):
    """
    Base class for NuoCA Multi-Process Plugins
    NuoCA plugins are based on Python Yapsy: http://yapsy.sourceforge.net/
    """

    def __init__(self, parent_pipe, plugin_name, plugin_type):
        """
        :param parent_pipe: Pipe setup by Yaspy
        :param plugin_name: Name of the plugin.
        :type plugin_name: ``str``
        :param plugin_type: Plugin type: one of: "Input", "Output", "Transform"
        :type plugin_type: ``str``
        """
        nuoca_log(logging.INFO, "Creating plugin: %s" % plugin_name)
        self._parent_pipe = parent_pipe
        self._plugin_name = plugin_name
        self._type = plugin_type
        self._enabled = False
        IMultiprocessChildPlugin.__init__(self, parent_pipe=parent_pipe)

    @property
    def plugin_name(self):
        return self._plugin_name

    @property
    def type(self):
        return self._type

    @property
    def enabled(self):
        return self._enabled

    @enabled.setter
    def enabled(self, value):
        self._enabled = value

    def activate(self):
        nuoca_log(logging.INFO, "Activate plugin: %s" % self.name)
        super(NuocaMPPlugin, self).activate()
        self._enabled = True

    def startup(self, config):
        raise NotImplementedError("Child class must implement startup method")

    def shutdown(self):
        raise NotImplementedError("Child class must implement shutdown method")

    def deactivate(self):
        nuoca_log(logging.INFO, "Deactivate plugin: %s" % self.name)
        super(NuocaMPPlugin, self).deactivate()
        self._enabled = False

    def has_required_config_items(self, config, required_config_items):
        """
        Check that the configuration contains the required items.

        :param config: Configuration to check
        :type config: ``dict``

        :param required_config_items: List of required configuration item names
        :type required_config_items: ``List[str]``

        :return: False if config or required items are missing.  Otherwise
        return True.
        """
        if not config:
            nuoca_log(logging.ERROR, "%s plugin: missing config file." %
                      self._plugin_name)
            return False
        for config_item in required_config_items:
            if config_item not in config:
                nuoca_log(logging.ERROR, "%s plugin: '%s' missing from config." %
                          (self._plugin_name, config_item))
                return False
        return True


class NuocaMPInputPlugin(NuocaMPPlugin):
    """
    NuoCA Multi-Process Input Plugin

    This is a base class for ALL NuoCA Input Plugins.

    All NuoCA Input Plugins must do:
      1) Implement a Class that derives from NuocaMPInputPlugin
      2) call this __init__ function from the Plugin's __init__.
      3) Implement a collect() method that calls this collect() method.
    """

    def __init__(self, parent_pipe, plugin_name):
        """
        :param parent_pipe: Provided by Yapsy
        :param plugin_name: Plugin name
        :type plugin_name: ``str``
        """
        super(NuocaMPInputPlugin, self).__init__(parent_pipe, plugin_name, "Input")
        self._collection_name = plugin_name

    def _send_response(self, status_code, err_msg=None, resp_dict=None):
        response = {'status_code': status_code}
        if err_msg:
            response['error_msg'] = err_msg
        if resp_dict:
            response['resp_values'] = resp_dict
        self.parent_pipe.send(response)

    def run(self):
        """
        This function is called by Yapsy
        """
        self.enabled = True
        nuoca_log(logging.INFO, "Plugin: %s,  PID: %d" % (self.plugin_name, os.getpid()))
        while self.enabled:
            try:
                request_from_parent = self.parent_pipe.recv()
                if not request_from_parent:
                    self._send_response(2, "Empty request from parent in Plugin: %s"
                                        % self.name)
                    continue
                if 'action' not in request_from_parent:
                    self._send_response(2, "Action missing from request in Plugin: %s"
                                        % self.name)
                    continue
                action = request_from_parent['action']
                if action == 'collect':
                    collection_interval = request_from_parent['collection_interval']
                    collected_values = self.collect(collection_interval)
                    self._send_response(0, None, {'collected_values': collected_values})
                    continue
                elif action == 'startup':
                    config = request_from_parent['config']
                    if config:
                        if 'nuocaCollectionName' in config:
                            self._collection_name = config['nuocaCollectionName']
                        if 'environmentVariables' in config:
                            for env_var in config['environmentVariables']:
                                os.environ[env_var['name']] = env_var['value']
                                msg = "Env: %s=%s" % (env_var['name'], env_var['value'])
                                nuoca_log(logging.INFO, msg)

                    startup_rval = self.startup(config)
                    self._send_response(int(not startup_rval))
                    continue
                elif action == 'shutdown':
                    self.shutdown()
                    continue
                elif action == 'exit':
                    self.enabled = False
                    self._send_response(0, None, {'goodbye': 'world'})
                    continue
                else:
                    self._send_response(2, "Action %s unknown in Plugin: %s"
                                        % (action, self.name))
                    continue

            except Exception as e:
                err_msg = "Unhandled exception: %s\n%s" % (e, traceback.format_exc())
                self._send_response(1, err_msg)

    def deactivate(self):
        super(NuocaMPInputPlugin, self).deactivate()

    def collect(self, collection_interval):
        """
        NuoCA Input Plugins must implement their own collect() method.  The
        NuoCA Input Plugins must call this collect() method at the top of
        their collect() method.  This method returns a python dictionary
        of values that each NuoCA Input Plugin should add to their own
        time-series information.

        Note: The plugin's collect() method must return a Python list
        of one or more Python dictionaries that contain time-series values.

        NuoCA will call the collect() method at the end of each Collection
        Interval.

        :param collection_interval: Collection Interval
        :type collection_interval: ``int``
        :return: time-series values
        :type: ``dict``
        """
        rval = {'collect_timestamp': nuoca_gettimestamp() * 1000}
        return rval


class NuocaMPOutputPlugin(NuocaMPPlugin):
    """
    NuoCA Multi-Process Output Plugin

    This is a base class for ALL NuoCA Output Plugins.

    All NuoCA Output Plugins must do:
      1) Implement a Class that derives from NuocaMPOutputPlugin
      2) call this __init__ function from the Plugin's __init__.
      3) Implement a store() method that calls this store() method.
    """

    def __init__(self, parent_pipe, plugin_name):
        super(NuocaMPOutputPlugin, self).__init__(parent_pipe, plugin_name,
                                                  "Output")

    def _send_response(self, status_code, err_msg=None, resp_dict=None):
        response = {'status_code': status_code}
        if err_msg:
            response['error_msg'] = err_msg
        if resp_dict:
            response['resp_values'] = resp_dict
        self.parent_pipe.send(response)

    def run(self):
        """
        This function is called by Yapsy
        """
        self.enabled = True
        nuoca_log(logging.INFO, "Plugin: %s,  PID: %d" % (self.plugin_name, os.getpid()))
        while self.enabled:
            try:
                request_from_parent = self.parent_pipe.recv()
                if not request_from_parent:
                    self._send_response(2, "Empty request from parent in Plugin: %s"
                                        % self.name)
                    continue
                if 'action' not in request_from_parent:
                    self._send_response(2, "Action missing from request in Plugin: %s"
                                        % self.name)
                    continue
                action = request_from_parent['action']
                if action == 'store':
                    ts_values = request_from_parent['ts_values']
                    resp_from_store = self.store(ts_values)
                    self._send_response(0, None, resp_from_store)
                    continue
                elif action == 'startup':
                    config = request_from_parent['config']
                    if config:
                        if 'environmentVariables' in config:
                            for env_var in config['environmentVariables']:
                                os.environ[env_var['name']] = env_var['value']
                                msg = "Env: %s=%s" % (env_var['name'], env_var['value'])
                                nuoca_log(logging.INFO, msg)

                    startup_rval = self.startup(config)
                    self._send_response(int(not startup_rval))
                    continue
                elif action == 'shutdown':
                    self.shutdown()
                    continue
                elif action == 'exit':
                    self.enabled = False
                    self._send_response(0, None, {'goodbye': 'world'})
                    continue
                else:
                    self._send_response(2, "Action %s unknown in Plugin: %s"
                                        % (action, self.name))
                    continue
            except Exception as e:
                err_msg = "Unhandled exception: %s\n%s" % (e, traceback.format_exc())
                self._send_response(1, err_msg)

    def store(self, ts_values):
        pass


class NuocaMPTransformPlugin(NuocaMPPlugin):
    """
    NuoCA Multi-Process Transformation Plugin
    """

    def __init__(self, parent_pipe, plugin_name):
        super(NuocaMPTransformPlugin, self).__init__(parent_pipe,
                                                     plugin_name, "Transform")
        raise Exception("Not Yet Implemented")
