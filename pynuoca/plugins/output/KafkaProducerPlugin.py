# Copyright (c) 2017-2020, NuoDB, Inc.
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

import logging
from kafka import KafkaProducer
import json

from pynuoca.nuoca_plugin import NuocaMPOutputPlugin
from pynuoca.nuoca_util import nuoca_log


class KafkaProducerPlugin(NuocaMPOutputPlugin):
    def __init__(self, parent_pipe, config=None):
        super(KafkaProducerPlugin, self).__init__(parent_pipe, 'KafkaProducer')
        self._config = config
        self._producer = None
        self._defaulttopic = None

    def startup(self, config=None):
        try:
            self._config = config

            servers = config.get('servers', 'localhost:9092')
            self._defaulttopic = config.get('defaulttopic', None)
            print servers
            self._producer = KafkaProducer(bootstrap_servers=servers,
                                           value_serializer=lambda v: json.dumps(v).encode('utf-8')
                                           )
            return True
        except Exception as e:
            nuoca_log(logging.ERROR, str(e))

    def shutdown(self):
        pass

    def store(self, ts_values):
        rval = None
        try:
            nuoca_log(logging.DEBUG,
                      "Called store() in KafkaProducerPlugin process")
            rval = super(KafkaProducerPlugin, self).store(ts_values)
            topic = self._defaulttopic
            if topic is not None:
                if type(ts_values) is list:
                    for svalues in ts_values:
                        self._producer.send(topic, svalues)
                else:
                    self._producer.send(topic, ts_values)
        except Exception as e:
            nuoca_log(logging.ERROR, str(e))
        return rval
