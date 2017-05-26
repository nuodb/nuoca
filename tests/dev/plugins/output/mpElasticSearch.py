import logging
from elasticsearch import Elasticsearch
from elasticsearch import helpers
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
      self.elastic_hosts = [{"host": "localhost",
                              "port": "9200"}]
      self.es_obj = Elasticsearch(self.elastic_hosts, timeout=10)
      logger = logging.getLogger('elasticsearch')
      logger.setLevel(logging.WARNING)
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
      req_resp = self.es_obj.index(index=self._config['INDEX'],
                                   doc_type='nuoca', body=ts_values)
      nuoca_log(logging.DEBUG, "ElasticSearch response: %s" % str(req_resp))
    except Exception as e:
      nuoca_log(logging.ERROR, str(e))
    return rval
