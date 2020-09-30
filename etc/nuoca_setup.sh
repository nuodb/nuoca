# (C) Copyright NuoDB, Inc. 2017-2018
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.
#
# This file should be _sourced_ by other scripts.

: "${NUOCA_HOME:?ERROR: NUOCA_HOME is not set!}"

if [ -f "$NUOCA_HOME"/etc/nuodb_setup.sh ]; then
    _home="$NUOCA_HOME"
elif [ -n "$NUOCLIENT_HOME" ] && [ -f "$NUOCLIENT_HOME"/etc/nuodb_setup.sh ]; then
    _home="$NUOCLIENT_HOME"
elif [ -n "$NUODB_HOME" ] && [ -f "$NUODB_HOME"/etc/nuodb_setup.sh ]; then
    _home="NUODB_HOME"
elif [ -f /opt/nuodb/etc/nuodb_setup.sh ]; then
    _home=/opt/nuodb
else
    echo "Cannot locate NuoDB installation"
    exit 1
fi

. "$_home"/etc/nuodb_setup.sh

: ${NUODB_PORT:=48004}
NUODB_DOMAIN_PASSWORD=${DOMAIN_PASSWORD:-bird}

: ${LOGSTASH_HOME:="$NUOCA_HOME/extern/logstash"}
: ${NUOADMIN_API_SERVER_NONSSL:="http://localhost:8888"}
: ${NUOADMIN_API_SERVER_SSL:="https://localhost:8888"}

if [ -z "$NUODB_NUOCA_CLIENT_KEY" ]; then
    if [ -f "$NUODB_CFGDIR/keys/nuodb_insights.pem" ]; then
        export NUODB_NUOCA_CLIENT_KEY="$NUODB_CFGDIR/keys/nuodb_insights.pem"
    elif [ -f  "$NUODB_CFGDIR/keys/nuocmd.pem" ]; then
        export NUODB_NUOCA_CLIENT_KEY="$NUODB_CFGDIR/keys/nuocmd.pem"
    fi
fi

NUOADMINAGENTLOGCONFIG="$NUOCA_HOME/etc/logstash/nuoadminagentlog.conf"

PATH="$PATH:$NUOCA_HOME/extern/zabbix/bin"

# This is if we're running from a Git repo or from PyPI
[ -d "$NUOCA_HOME/pynuoca/lib" ] \
    && PYTHONPATH="${PYTHONPATH:+$PYTHONPATH:}$NUOCA_HOME"

# This is if we're running from an unpacked NuoDB package
[ -d "$_home/etc/python/site-packages" ] \
    && PYTHONPATH="${PYTHONPATH:+$PYTHONPATH:}$_home/etc/python/site-packages"

# See if we can locate nuopython
if [ -x "$_home"/etc/python/nuopython ]; then
    PYTHONCMD="$_home"/etc/python/nuopython
elif [ -n "$NUODB_HOME" ] && [ -x "NUODB_HOME"/etc/python/nuopython ]; then
    PYTHONCMD="$NUODB_HOME"/etc/python/nuopython
else
    PYTHONCMD=python
fi

unset _home
