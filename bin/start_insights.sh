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
    export INSIGHTS_SUB_ID=`cat ${NUODB_CFGDIR}/insights.sub.id`
    export INSIGHTS_INGEST_URL=`cat ${NUODB_CFGDIR}/insights.sub.ingest_url`
    "${NUOCA_HOME}/bin/start_zabbix_agentd.sh"
    python "${NUOCA_HOME}/src/nuoca.py" --mode insights -o sub_id=${INSIGHTS_SUB_ID} --collection-interval 30 "${NUOCA_HOME}/etc/nuodb_domain.yml" > /dev/null 2>&1 &
    NUOCA_PID=$!
    echo "$NUOCA_PID" > "${NUODB_RUNDIR}/nuoca.pid"
  fi
fi
