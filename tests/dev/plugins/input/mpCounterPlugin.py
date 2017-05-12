from nuoca_plugin import NuocaMPInputPlugin

class MPCounterPlugin(NuocaMPInputPlugin):
  def __init__(self, parent_pipe):
    super(MPCounterPlugin, self).__init__(parent_pipe, 'CounterPlugin' )
    self.counter = 0

  def increment(self):
    self.counter += 1

  def get_count(self):
    return self.counter

  def collect(self):
    rval = super(MPCounterPlugin, self).collect()
    self.increment()
    rval["counter"] = self.get_count()
    return rval