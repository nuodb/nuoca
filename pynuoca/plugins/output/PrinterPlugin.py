# (C) Copyright NuoDB, Inc. 2017-2020
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.

import logging
from pynuoca.nuoca_plugin import NuocaMPOutputPlugin
from pynuoca.nuoca_util import nuoca_log


class PrinterPlugin(NuocaMPOutputPlugin):
    def __init__(self, parent_pipe, config=None):
        super(PrinterPlugin, self).__init__(parent_pipe, 'Printer')
        self._config = config

    def startup(self, config=None):
        try:
            self._config = config
            return True
        except Exception as e:
            nuoca_log(logging.ERROR, str(e))
            return False

    def shutdown(self):
        pass

    def store(self, ts_values):
        rval = None
        try:
            nuoca_log(logging.DEBUG, "Called store() in MPCounterPlugin process")
            rval = super(PrinterPlugin, self).store(ts_values)
            print(ts_values)
        except Exception as e:
            nuoca_log(logging.ERROR, str(e))
        return rval
