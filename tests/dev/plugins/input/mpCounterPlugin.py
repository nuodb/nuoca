import logging
from nuoca_plugin import NuocaMPInputPlugin
from nuoca_util import nuoca_log


class MPCounterPlugin(NuocaMPInputPlugin):
  def __init__(self, parent_pipe):
    super(MPCounterPlugin, self).__init__(parent_pipe, 'CounterPlugin')
    self._config = None
    self._count = 0
    self._increment_value = 1

  def startup(self, config=None):
    try:
      self._config = config
      if config:
        if 'increment' in config:
          self._increment_value = int(config['increment'])
      return True
    except Exception as e:
      nuoca_log(logging.ERROR, str(e))
      return False

  def shutdown(self):
    pass

  def increment(self):
    self._count += self._increment_value

  def get_count(self):
    return self._count

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
