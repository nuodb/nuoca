#!/bin/sh

# Find the NuoCA home directory.
CMD=${0##*/}
DIR=`cd "${0%$CMD}." && pwd`
NUOCA_HOME=${DIR%/*}

. "${NUOCA_HOME}/etc/nuoca_setup.sh"
. "${NUOCA_HOME}/etc/nuoca_export.sh"

export DOMAIN_USER=domain

RESPONSE=`python  "${NUOCA_HOME}/src/insights.py" startup`
if [ "$RESPONSE" = "Startup" ]; then
  nuocaCount=$(ps -ef | grep "${NUOCA_HOME}/src/nuoca.py" | wc -l)
  if [ $nuocaCount -le 1 ]; then
    echo "Starting NuoCA"
    export ES_URL=`cat ${NUODB_CFGDIR}/insights.sub.elastic_url`
    export ES_PORT="9200"
    export ES_INDEX="ic"
    export EX_PIPELINE="ic"
    "${NUOCA_HOME}/bin/start_zabbix_agentd.sh"
    python "${NUOCA_HOME}/src/nuoca.py" --mode insights --collection-interval 30 "${NUOCA_HOME}/etc/nuodb_domain.yml" > /dev/null 2>&1 &
    NUOCA_PID=$!
    echo "$NUOCA_PID" > "${NUODB_RUNDIR}/nuoca.pid"
  fi
fi
