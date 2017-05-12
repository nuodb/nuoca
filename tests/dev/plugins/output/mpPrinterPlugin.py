from nuoca_plugin import NuocaMPOutputPlugin

class MPPrinterPlugin(NuocaMPOutputPlugin):
  def __init__(self, parent_pipe):
    super(MPPrinterPlugin, self).__init__(parent_pipe, 'PrinterPlugin')

  def store(self, ts_values):
    rval = super(MPPrinterPlugin, self).store(ts_values)
    print(ts_values)
    return rval
