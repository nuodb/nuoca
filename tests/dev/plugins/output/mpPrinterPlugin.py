import logging
from nuoca_plugin import NuocaMPOutputPlugin
from nuoca_util import nuoca_log

class MPPrinterPlugin(NuocaMPOutputPlugin):
  def __init__(self, parent_pipe):
    super(MPPrinterPlugin, self).__init__(parent_pipe, 'PrinterPlugin')

  def store(self, ts_values):
    rval = None
    try:
      rval = super(MPPrinterPlugin, self).store(ts_values)
      nuoca_log(logging.DEBUG, "Called store() in MPCounterPlugin process")
      print(ts_values)
    except Exception as e:
      nuoca_log(logging.ERROR, str(e))
    return rval
