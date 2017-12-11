# (C) Copyright NuoDB Inc. 2017  All Rights Reserved.
#
# This file should be _sourced_ by other scripts.

: "${NUOCA_HOME?ERROR: NUOCA_HOME is not set!}"

NUODB_HOME=${NUODB_HOME:-"/opt/nuodb"}

. "${NUODB_HOME}/etc/nuodb_setup.sh"

LOGSTASH_HOME=${LOGSTASH_HOME:-"${NUOCA_HOME}/logstash"}
NUODB_PORT=${NUODB_PORT:-48004}
NUODB_DOMAIN_PASSWORD=${DOMAIN_PASSWORD:-bird}

# Are we running the python that we built in nuo3rdparty?
if [ -d ${NUOCA_HOME}/python ]; then
  PATH="${NUOCA_HOME}/python/bin:${PATH}"
  PYTHONHOME="${NUOCA_HOME}/python:${NUOCA_HOME}/python/x86_64-linux"
fi

PATH="${PATH}:${NUOCA_HOME}/zabbix/bin"
PYTHONPATH="${NUOCA_HOME}/src:${NUOCA_HOME}:${NUOCA_HOME}/lib"
NUOADMINAGENTLOGCONFIG="${NUOCA_HOME}/etc/logstash/nuoadminagentlog.conf"
NUODB_INSIGHTS_SERVICE_API=${NUODB_INSIGHTS_SERVICE_API:-"http://18.217.51.252/api/1"}
