import logging
from nuoca_plugin import NuocaMPOutputPlugin
from nuoca_util import nuoca_log


class MPPrinterPlugin(NuocaMPOutputPlugin):
  def __init__(self, parent_pipe, config=None):
    super(MPPrinterPlugin, self).__init__(parent_pipe, 'PrinterPlugin')
    self._config = config

  def startup(self, config=None):
    try:
      self._config = config
      return True
    except Exception as e:
      nuoca_log(logging.ERROR, str(e))
      return False

  def shutdown(self):
    pass

  def store(self, ts_values):
    rval = None
    try:
      nuoca_log(logging.DEBUG, "Called store() in MPCounterPlugin process")
      rval = super(MPPrinterPlugin, self).store(ts_values)
      print(ts_values)
    except Exception as e:
      nuoca_log(logging.ERROR, str(e))
    return rval
