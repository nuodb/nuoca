import logging
import requests
from nuoca_plugin import NuocaMPOutputPlugin
from nuoca_util import nuoca_log


class MPElasticSearch(NuocaMPOutputPlugin):
  def __init__(self, parent_pipe, config=None):
    super(MPElasticSearch, self).__init__(parent_pipe, 'ElasticSearch')
    self._config = config

  def startup(self, config=None):
    try:
      self._config = config
      if not self._config:
        nuoca_log(logging.ERROR,
                  "MPElasticSearch plugin configuration missing")
        return False
      if 'URI' not in self._config:
        nuoca_log(logging.ERROR,
                  "MPElasticSearch plugin URI configuration missing")
        return False
      if 'INDEX' not in self._config:
        nuoca_log(logging.ERROR,
                  "MPElasticSearch plugin INDEX configuration missing")
        return False
      self._url = self._config['URI'] + '/' + self._config['INDEX']
      return True
    except Exception as e:
      nuoca_log(logging.ERROR, str(e))
      return False

  def shutdown(self):
    pass

  def store(self, ts_values):
    rval = None
    try:
      nuoca_log(logging.DEBUG, "Called store() in MPElasticSearch process")
      rval = super(MPElasticSearch, self).store(ts_values)
      req_resp = requests.put(self._url, data=ts_values)
    except Exception as e:
      nuoca_log(logging.ERROR, str(e))
    return rval
