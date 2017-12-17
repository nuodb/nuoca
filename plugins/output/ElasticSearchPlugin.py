# Copyright (c) 2017, NuoDB, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of NuoDB, Inc. nor the names of its contributors may
#       be used to endorse or promote products derived from this software
#       without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL NUODB, INC. BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA,
# OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
# ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import os
import logging
from elasticsearch import Elasticsearch
from elasticsearch import helpers
from nuoca_plugin import NuocaMPOutputPlugin
from nuoca_util import nuoca_log


class ElasticSearchPlugin(NuocaMPOutputPlugin):
  def __init__(self, parent_pipe, config=None):
    super(ElasticSearchPlugin, self).__init__(parent_pipe, 'ElasticSearch')
    self._config = config
    self.elastic_hosts = None
    self.es_obj = None
    self.es_index = None
    self.es_index_pipeline = None
    self.ES_LIMIT_SIZE = 1000
    self.ES_BULK_CHUNK_SIZE = 75
    self.ES_BULK_CHUNK_BYTES = 6291456

  def startup(self, config=None):
    try:
      self._config = config
      required_config_items = ['HOST', 'PORT', 'INDEX']
      if not self.has_required_config_items(config, required_config_items):
        return False
      if 'PIPELINE' in config:
        self.es_index_pipeline = os.path.expandvars(config['PIPELINE'])
      host = os.path.expandvars(self._config['HOST'])
      if isinstance(self._config['PORT'], int):
        port = self._config['PORT']
      else:
        port = os.path.expandvars(self._config['PORT'])
      self.es_index = os.path.expandvars(self._config['INDEX'])
      self.elastic_hosts = [{"host": host, "port": port}]
      self.es_obj = Elasticsearch(self.elastic_hosts, timeout=10)
      logger = logging.getLogger('elasticsearch')
      logger.setLevel(logging.WARNING)
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
