"""
Created on May 4, 2017

@author: tgates
"""

import json
import traceback
import logging
from nuoca_util import nuoca_gettimestamp, nuoca_log
from yapsy.IMultiprocessChildPlugin import IMultiprocessChildPlugin


class NuocaMPPlugin(IMultiprocessChildPlugin):
  """
  Base class for NuoCA Multi-Process Plugins
  NuoCA plugins are based on Python Yapsy: http://yapsy.sourceforge.net/
  """
  def __init__(self, parent_pipe, name, plugin_type):
    nuoca_log(logging.INFO, "Creating plugin: %s" % name)
    self._parent_pipe = parent_pipe
    self._name = name
    self._type = plugin_type
    self._enabled = False
    IMultiprocessChildPlugin.__init__(self, parent_pipe=parent_pipe)

  @property
  def name(self):
    return self._name

  @property
  def type(self):
    return self._type

  @property
  def enabled(self):
    return self._enabled

  def activate(self):
    nuoca_log(logging.INFO, "Activate plugin: %s" % self.name)
    super(NuocaMPPlugin, self).activate()
    self._enabled = True

  def deactivate(self):
    nuoca_log(logging.INFO, "Deactivate plugin: %s" % self.name)
    super(NuocaMPPlugin, self).deactivate()
    self._enabled = False


class NuocaMPInputPlugin(NuocaMPPlugin):
  """
  NuoCA Multi-Process Input Plugin

  This is a base class for ALL NuoCA Input Plugins.

  All NuoCA Input Plugins must do:
    1) Implement a Class that derives from NuocaMPInputPlugin
    2) call this __init__ function from the Plugin's __init__.
    3) Implement a collect() method that calls this collect() method.
  """
  def __init__(self, parent_pipe, name):
    """
    :param parent_pipe: Provided by Yapsy
    :param name: Plugin name
    :type name: ``str``
    """
    super(NuocaMPInputPlugin, self).__init__(parent_pipe, name, "Input")

  def run(self):
    """
    This function is called by Yapsy
    """
    self._enabled = True
    while self.enabled:
      collected_values = None
      response = {}
      try:
        content_from_parent = self.parent_pipe.recv()
        if content_from_parent == "collect":
          collected_values = self.collect()
          response["status_code"] = 0
          response["collected_values"] = collected_values
        elif content_from_parent == "exit":
          self._enabled = False
          response["status_code"] = 0
          response["collected_values"] = collected_values
        else:
          response["status_code"] = 2
          response["error_msg"] = \
            "NuoCA Message '%s' unknown" % \
                                 content_from_parent
      except Exception as e:
        response["status_code"] = 1
        response["error_msg"] = "Unhandled exception: %s" % e
        response["stack_trace"] = traceback.format_exc()
      resp_msg = json.dumps(response)
      self.parent_pipe.send(resp_msg)

  def deactivate(self):
    super(NuocaMPInputPlugin, self).deactivate()

  def collect(self):
    """
    NuoCA Plugins must implement their own collect() function and also call
    this collect() function.  The collect function must return a Python
    dictionary of time-series values.

    NuoCA will call this function once at the beginning of each Collection
    Interval.
    :return: time-series values
    :type: ``dict``
    """
    rval = {"nuoca_plugin": self.name,
            "collect_timestamp": nuoca_gettimestamp()}
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
  def __init__(self, parent_pipe, name):
    super(NuocaMPOutputPlugin, self).__init__(parent_pipe, name, "Output")

  def _send_response(self, status_code, err_msg=None, resp_dict=None):
    response = {"status_code": status_code}
    if err_msg:
      response["error_msg"] = err_msg
    if resp_dict:
      response["resp_values"] = resp_dict
    resp_msg = json.dumps(response)
    self.parent_pipe.send(resp_msg)

  def run(self):
    """
    This function is called by Yapsy
    """
    self._enabled = True
    while self.enabled:
      collected_values = None
      response = {}
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
        if action == "store":
          ts_values = request_from_parent['ts_values']
          resp_from_store = self.store(ts_values)
          self._send_response(0, None, resp_from_store)
          continue
        elif action == "exit":
          self._enabled = False
          self._send_response(0, None, {"goodbye": "world"})
          continue
        else:
          self._send_response(2, "Action %s unknown in Plugin: %s"
                              % (action, self.name))
          continue
      except Exception as e:
        response["status_code"] = 1
        response["error_msg"] = "Unhandled exception: %s" % e
        response["stack_trace"] = traceback.format_exc()
        resp_msg = json.dumps(response)
        self.parent_pipe.send(resp_msg)

  def store(self, ts_values):
    pass


class NuocaMPTransformPlugin(NuocaMPPlugin):
  """
  NuoCA Multi-Process Transformation Plugin
  """
  def __init__(self, parent_pipe, name):
    super(NuocaMPTransformPlugin, self).__init__(parent_pipe,
                                                 name, "Transform")
    raise Exception("Not Yet Implemented")


