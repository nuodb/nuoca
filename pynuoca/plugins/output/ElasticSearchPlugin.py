# (C) Copyright NuoDB, Inc. 2017-2020
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.

import os
import logging
from elasticsearch import Elasticsearch
from elasticsearch import helpers
from pynuoca.nuoca_plugin import NuocaMPOutputPlugin
from pynuoca.nuoca_util import nuoca_log


class ElasticSearchPlugin(NuocaMPOutputPlugin):
    def __init__(self, parent_pipe, config=None):
        super(ElasticSearchPlugin, self).__init__(parent_pipe, 'ElasticSearch')
        self._config = config
        self.elastic_hosts = None
        self.port = None
        self.url_prefix = None
        self.es_obj = None
        self.es_index = None
        self.es_index_pipeline = None
        self.ES_LIMIT_SIZE = 1000
        self.ES_BULK_CHUNK_SIZE = 75
        self.ES_BULK_CHUNK_BYTES = 6291456

    def startup(self, config=None):
        try:
            logger = logging.getLogger('elasticsearch')
            logger.setLevel(logging.WARNING)
            self._config = config
            required_config_items = ['HOST', 'INDEX']
            if not self.has_required_config_items(config, required_config_items):
                return False
            if 'PIPELINE' in config:
                self.es_index_pipeline = os.path.expandvars(config['PIPELINE'])
            host = os.path.expandvars(self._config['HOST'])
            if 'PORT' in self._config:
                if isinstance(self._config['PORT'], int):
                    self.port = self._config['PORT']
                else:
                    self.port = os.path.expandvars(self._config['PORT'])
            if 'URL_PREFIX' in config:
                self.url_prefix = os.path.expandvars(self._config['URL_PREFIX'])
            self.es_index = os.path.expandvars(self._config['INDEX'])
            elastic_host = {'host': host}
            if self.port:
                elastic_host['port'] = self.port
            if self.url_prefix:
                elastic_host['url_prefix'] = self.url_prefix
            self.elastic_hosts = [elastic_host]
            self.es_obj = Elasticsearch(self.elastic_hosts, timeout=10)
            return True
        except Exception as e:
            nuoca_log(logging.ERROR, "ElasticSearch Store error: %s" % str(e))
            return False

    def shutdown(self):
        pass

    def _bulk_index(self, ts_values):
        offset = 0
        total = 0
        b_complete = False
        limit_size = self.ES_LIMIT_SIZE
        update_count = 0
        total = len(ts_values)
        es_index = self.es_index
        if self.es_index_pipeline:
            es_index
        while not b_complete:
            actions = []
            items_to_process = limit_size
            if offset + limit_size > total:
                items_to_process = total - offset
            for i in range(items_to_process):
                row = ts_values[i]
                action = {"_index": es_index,
                          "_type": "nuoca",
                          "_source": row}
                actions.append(action)
            if len(actions) > 0:
                resp = helpers.bulk(self.es_obj,
                                    actions,
                                    chunk_size=self.ES_BULK_CHUNK_SIZE,
                                    max_chunk_bytes=self.ES_BULK_CHUNK_BYTES)
                nuoca_log(logging.DEBUG, "ES bluk response: %s" % str(resp))
                update_count += resp[0]
            if offset + items_to_process >= total:
                b_complete = True
            offset += limit_size
        nuoca_log(logging.DEBUG, "ES Indexed %d documents" % update_count)

    def store(self, ts_values):
        rval = None
        try:
            nuoca_log(logging.DEBUG, "Called store() in NuoCA ElasticSearch process")
            rval = super(ElasticSearchPlugin, self).store(ts_values)
            self._bulk_index(ts_values)
        except Exception as e:
            nuoca_log(logging.ERROR, str(e))
        return rval
