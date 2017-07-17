import logging
import requests
import json

from nuoca_plugin import NuocaMPOutputPlugin
from nuoca_util import nuoca_log

class MPRestClientOutputPlugin(NuocaMPOutputPlugin):
  def __init__(self, parent_pipe, config=None):
    super(MPRestClientOutputPlugin, self).__init_(parent_pipe, 'RestClient')
    super._config = config

  def startup(self, config=None):
    try:
      self._config = config
      return True
    except Exception as e:
      nuoca_log(logging.ERROR, str(e))

  def shutdown(self):
    pass

  def store(self, ts_values):
    rval = None
    try:
      nuoca_log(logging.DEBUG, "Called store() in MPClientOutputPlugin process")
      rval = super(MPRestClientOutputPlugin, self).store(ts_values)
      requests.post(self._config["url"], json=json.dumps(ts_values))
    except Exception as e:
      nuoca_log(logging.ERROR, str(e))
    return rval
