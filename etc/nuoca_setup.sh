# (C) Copyright NuoDB Inc. 2017  All Rights Reserved.
#
# This file should be _sourced_ by other scripts.

: "${NUOCA_HOME:?ERROR: NUOCA_HOME is not set!}"

# See if we're running nuoca from within a NuoDB package
if [ -z "$NUODB_HOME" ]; then
    case $NUOCA_HOME in
        (*/etc/nuoca)
            if [ -f "$NUOCA_HOME/../../etc/nuodb_setup.sh" ]; then
                NUODB_HOME=${NUOCA_HOME%/etc/nuoca}
            fi ;;
        (*) : not NuoDB ;;
    esac
    : ${NUODB_HOME:=/opt/nuodb}
fi

[ -f "$NUODB_HOME/etc/nuodb_setup.sh" ] || { echo "Invalid NUODB_HOME: $NUODB_HOME"; exit 1; }
. "${NUODB_HOME}/etc/nuodb_setup.sh"

: ${NUODB_PORT:=48004}
NUODB_DOMAIN_PASSWORD=${DOMAIN_PASSWORD:-bird}

: ${LOGSTASH_HOME:="${NUOCA_HOME}/logstash"}
: ${NUODB_INSIGHTS_SERVICE_API:="http://insights.nuodb.com/api/1"}

PATH="${PATH}:${NUOCA_HOME}/zabbix/bin"
PYTHONPATH="${NUOCA_HOME}/src:${NUOCA_HOME}:${NUOCA_HOME}/lib"
NUOADMINAGENTLOGCONFIG="${NUOCA_HOME}/etc/logstash/nuoadminagentlog.conf"

# Are we running Python included in the NuoDB package?
_pypath="${NUOCA_HOME%/*}/python"
PYTHONCMD="$_pypath/nuopython"
if [ -x "$PYTHONCMD" ]; then
    PATH="${_pypath}/bin:${PATH}"
    PYTHONHOME="${_pypath}:${_pypath}/x86_64-linux"
else
    PYTHONCMD=python
fi
unset _pypath
