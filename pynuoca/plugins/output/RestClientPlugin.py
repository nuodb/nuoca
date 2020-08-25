# (C) Copyright NuoDB, Inc. 2017-2020
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.

import os
import logging
import requests
import json

from pynuoca.nuoca_plugin import NuocaMPOutputPlugin
from pynuoca.nuoca_util import nuoca_log


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
            headers = {"content-type": "application/json"}
            if self._auth_token:
                headers['Authorization'] = "Bearer %s" % self._auth_token
            requests.post(self._url, json=ts_values,
                          headers=headers)
        except Exception as e:
            nuoca_log(logging.ERROR, str(e))
        return rval
