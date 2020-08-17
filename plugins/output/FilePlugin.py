# (C) Copyright NuoDB, Inc. 2017-2020
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.

import os
import logging
import json

from pynuoca.nuoca_plugin import NuocaMPOutputPlugin
from pynuoca.nuoca_util import nuoca_log


class FilePlugin(NuocaMPOutputPlugin):
    def __init__(self, parent_pipe, config=None):
        super(FilePlugin, self).__init__(parent_pipe, 'File')
        self._config = config
        self._file_path = None
        self._fp = None

    def startup(self, config=None):
        try:
            self._config = config
            required_config_items = ['filePath']
            if not self.has_required_config_items(config, required_config_items):
                return False
            self._file_path = os.path.expandvars(config['filePath'])
            self._fp = open(self._file_path, 'w')
            return True
        except Exception as e:
            nuoca_log(logging.ERROR, str(e))
            return False

    def shutdown(self):
        if self._fp:
            self._fp.close()
            self._fp = None

    def store(self, ts_values):
        rval = None
        try:
            nuoca_log(logging.DEBUG, "Called store() in MPCounterPlugin process")
            rval = super(FilePlugin, self).store(ts_values)
            json.dump(ts_values, self._fp)
            self._fp.write("\n")

        except Exception as e:
            nuoca_log(logging.ERROR, str(e))
        return rval
