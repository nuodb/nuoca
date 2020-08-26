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
from pynuoca.nuoca_plugin import NuocaMPOutputPlugin
from pynuoca.nuoca_util import nuoca_log
import requests
from pynuoca.lib import metrics_influx
import gzip

try:
    from cStringIO import StringIO
except:
    from StringIO import StringIO
from distutils.util import strtobool
from requests.auth import HTTPBasicAuth


class InfluxDBPlugin(NuocaMPOutputPlugin):
    def __init__(self, parent_pipe, config=None):
        super(InfluxDBPlugin, self).__init__(parent_pipe, 'InfluxDB')
        self._config = config

    def startup(self, config=None):
        try:
            self._config = config
            cvalue = self._config.get('compress', 'False')
            self._compress = strtobool(str(cvalue))
            self._user = self._config.get('user', None)
            self._password = self._config.get('password', None)

            required_config_items = ['url']
            if not self.has_required_config_items(config, required_config_items):
                return False

            good = self._password is None if self._user is None else self._password is not None
            if not good:
                nuoca_log(logging.ERROR,
                          "%s plugin: if user specified in config, password must be also and vice versa" %
                          (self._plugin_name))
            return good
        except Exception as e:
            nuoca_log(logging.ERROR, str(e))
            return False

    def shutdown(self):
        pass

    def format(self, ts_values):
        pass

    def store(self, ts_values):

        rval = None
        try:
            nuoca_log(logging.DEBUG, "Called store() in NuoCA InfluxDBPlugin process")
            rval = super(InfluxDBPlugin, self).store(ts_values)

            # metrics_influx only formats data from NuoMon.
            # need to look at handling ZBX also.

            def write(fileobj):
                for single_values in ts_values:
                    values = dict([(k[7:], v) for k, v in single_values.iteritems() if k.startswith("NuoMon.")])
                    if len(values) == 0:
                        continue
                    contentType, message = metrics_influx.format(values)
                    fileobj.write(message)

            s = StringIO()
            if self._compress:
                with gzip.GzipFile(fileobj=s, mode='wb') as f:
                    write(f)
                headers = {"Content-Encoding": "gzip",
                           "Content-Type": "text/plain; charset=utf-8"
                           }
            else:
                write(s)
                headers = {"Content-Type": "text/plain; charset=utf-8"}

            mbuffer = s.getvalue()
            s.close()
            url = self._config['url']
            if self._user is not None:
                arg = requests.post(url, headers=headers, data=mbuffer, auth=HTTPBasicAuth(self._user, self._password))
            else:
                arg = requests.post(url, headers=headers, data=mbuffer)

            if arg.status_code not in [200, 204]:
                nuoca_log(logging.ERROR, "%d : %s" % (arg.status_code, arg.text))
        except Exception as e:
            nuoca_log(logging.ERROR, str(e))
        return rval
