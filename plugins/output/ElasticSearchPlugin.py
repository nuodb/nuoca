import logging
from elasticsearch import Elasticsearch
from nuoca_plugin import NuocaMPOutputPlugin
from nuoca_util import nuoca_log


class ElasticSearchPlugin(NuocaMPOutputPlugin):
  def __init__(self, parent_pipe, config=None):
    super(ElasticSearchPlugin, self).__init__(parent_pipe, 'ElasticSearch')
    self._config = config
    self.elastic_hosts = None
    self.es_obj = None
    self.es_index_pipeline = None

  def startup(self, config=None):
    try:
      self._config = config
      required_config_items = ['HOST', 'PORT', 'INDEX']
      if not self.has_required_config_items(config, required_config_items):
        return False
      if 'PIPELINE' in config:
        self.es_index_pipeline = config['PIPELINE']
      self.elastic_hosts = [{"host": self._config['HOST'],
                             "port": self._config['PORT']}]
      self.es_obj = Elasticsearch(self.elastic_hosts, timeout=10)
      logger = logging.getLogger('elasticsearch')
      logger.setLevel(logging.WARNING)
      return True
    except Exception as e:
      nuoca_log(logging.ERROR, "ElasticSearch Store error: %s" % str(e))
      return False

  def shutdown(self):
    pass

  def store(self, ts_values):
    rval = None
    try:
      nuoca_log(logging.DEBUG, "Called store() in MPElasticSearch process")
      rval = super(ElasticSearchPlugin, self).store(ts_values)
      req_resp = self.es_obj.index(index=self._config['INDEX'],
                                   doc_type='nuoca', body=ts_values,
                                   pipeline=self.es_index_pipeline)
      nuoca_log(logging.DEBUG, "ElasticSearch response: %s" % str(req_resp))
    except Exception as e:
      nuoca_log(logging.ERROR, str(e))
    return rval
