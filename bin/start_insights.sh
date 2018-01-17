#!/bin/sh

# (C) Copyright NuoDB, Inc. 2017-2018
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.

# Find the NuoCA home directory.
CMD=${0##*/}
DIR=`cd "${0%$CMD}." && pwd`
NUOCA_HOME=${DIR%/*}

. "${NUOCA_HOME}/etc/nuoca_setup.sh"
. "${NUOCA_HOME}/etc/nuoca_export.sh"

# Setup logstash if it has not been setup.
if [ ! -d "${NUOCA_HOME}/logstash" ]; then
  (cd "${NUOCA_HOME}" && ./bin/setup_logstash.sh)
fi

export DOMAIN_USER=domain

RESPONSE=`"$PYTHONCMD" "${NUOCA_HOME}/src/insights.py" startup`
if [ "$RESPONSE" = "Startup" ]; then
  # make sure the REST API is running
  "$NUODB_HOME"/etc/nuorestsvc start

  # Check to see if nuoca is already running
  nuocaCount=$(ps -ef | grep "${NUOCA_HOME}/src/nuoca.py" | wc -l)
  if [ $nuocaCount -le 1 ]; then
    # Set default nuoca settings.yml if not set.
    if [ ! -f "${NUODB_CFGDIR}/nuoca_settings.yml" ]; then
      cp "${NUOCA_HOME}/etc/insights.default.nuoca_settings.yml" "${NUODB_CFGDIR}/nuoca_settings.yml"
    fi
    echo "Starting NuoCA"
    export INSIGHTS_SUB_ID=`cat ${NUODB_CFGDIR}/insights.sub.id`
    export INSIGHTS_INGEST_URL=`cat ${NUODB_CFGDIR}/insights.sub.ingest_url`
    export INSIGHTS_TOKEN=`cat ${NUODB_CFGDIR}/insights.sub.token`
    "${NUOCA_HOME}/bin/start_zabbix_agentd.sh"
    "$PYTHONCMD" "${NUOCA_HOME}/src/nuoca.py" --mode insights -o sub_id=${INSIGHTS_SUB_ID} --collection-interval 30 "${NUOCA_HOME}/etc/nuodb_domain.yml" > /dev/null 2>&1 &
    NUOCA_PID=$!
    echo "$NUOCA_PID" > "${NUODB_RUNDIR}/nuoca.pid"
  fi
fi
