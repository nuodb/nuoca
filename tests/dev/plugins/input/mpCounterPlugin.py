import logging
from nuoca_plugin import NuocaMPInputPlugin
from nuoca_util import nuoca_log

class MPCounterPlugin(NuocaMPInputPlugin):
  def __init__(self, parent_pipe):
    super(MPCounterPlugin, self).__init__(parent_pipe, 'CounterPlugin' )
    self.counter = 0

  def increment(self):
    self.counter += 1

  def get_count(self):
    return self.counter

  def collect(self, collection_interval):
    rval = None
    try:
      nuoca_log(logging.DEBUG, "Called collect() in MPCounterPlugin process")
      rval = super(MPCounterPlugin, self).collect(collection_interval)
      self.increment()
      rval["counter"] = self.get_count()
    except Exception as e:
      nuoca_log(logging.ERROR, str(e))
    return rval