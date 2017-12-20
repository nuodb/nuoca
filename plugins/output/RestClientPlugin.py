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
import requests
import json

from nuoca_plugin import NuocaMPOutputPlugin
from nuoca_util import nuoca_log


class RestClientPlugin(NuocaMPOutputPlugin):
  def __init__(self, parent_pipe, config=None):
    super(RestClientPlugin, self).__init__(parent_pipe, 'RestClient')
    self._config = config
    self._url = None
    self._auth_token = None

  def startup(self, config=None):
    try:
      self._config = config
      required_config_items = ['url']
      if not self.has_required_config_items(config, required_config_items):
        return False
      self._url = os.path.expandvars(config['url'])
      if 'auth_token' in config:
        self._auth_token = os.path.expandvars(config['auth_token'])
      return True
    except Exception as e:
      nuoca_log(logging.ERROR, str(e))

  def shutdown(self):
    pass

  def store(self, ts_values):
    rval = None
    try:
      nuoca_log(logging.DEBUG,
                "Called store() in RestClientPlugin process")
      rval = super(RestClientPlugin, self).store(ts_values)
      headers = {"content-type":"application/json"}
      if self._auth_token:
        headers['Authorization'] = "Bearer %s" % self._auth_token
      requests.post(self._url, json=ts_values,
                    headers=headers)
    except Exception as e:
      nuoca_log(logging.ERROR, str(e))
    return rval
