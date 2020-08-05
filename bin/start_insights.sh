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
. "${NUOCA_HOME}/etc/utils.sh"

get_nuodb_user_group
log_user
get_nuoagent_creds

beginswith() { case $2 in "$1"*) true;; *) false;; esac; }

RESPONSE=`"$PYTHONCMD" "${NUOCA_HOME}/pynuoca/insights.py" startup`

if beginswith "Startup" $RESPONSE; then
  log_msg "INFO" "start_insights.sh: Insights startup requested."

  # Setup logstash if it has not been setup.
  if [ ! -d "${NUOCA_HOME}/extern/logstash" ]; then
    (cd "${NUOCA_HOME}" && ./bin/setup_logstash.sh)
  fi

  export INSIGHTS_SUB_ID=`cat "${NUODB_CFGDIR}/insights.sub.id"`
  export INSIGHTS_INGEST_URL=`cat "${NUODB_CFGDIR}/insights.sub.ingest_url"`
  export INSIGHTS_TOKEN=`cat "${NUODB_CFGDIR}/insights.sub.token"`
  export NUOCA_LOGFILE="${NUODB_LOGDIR}/nuoca.log"
  export NUOCA_CONFIG_FILE="${NUOCA_HOME}/etc/nuodb_domain.yml"

  # If new Admin, then use NuoCA nuoca_nuoadmin.yml config file
  if [ "$RESPONSE" = "Startup nuoadmin" ]; then
    export NUODB_API_SERVER="localhost:8888"
    export NUOCA_CONFIG_FILE="${NUOCA_HOME}/etc/nuoca_nuoadmin.yml"
  else
    # make sure the REST API is running
    "$NUODB_HOME"/etc/nuorestsvc start
  fi

  # Check to see if nuoca is already running
  nuocaCount=$(ps -ef | grep "${NUOCA_HOME}/pynuoca/nuoca.py" | wc -l)
  if [ $nuocaCount -le 1 ]; then
    # Set default nuoca settings.yml if not set.
    if [ ! -f "${NUODB_CFGDIR}/nuoca_settings.yml" ]; then
      cp "${NUOCA_HOME}/etc/insights.default.nuoca_settings.yml" "${NUODB_CFGDIR}/nuoca_settings.yml"
    fi
    echo "Starting NuoCA"
    export INSIGHTS_SUB_ID=`cat "${NUODB_CFGDIR}/insights.sub.id"`
    export INSIGHTS_INGEST_URL=`cat "${NUODB_CFGDIR}/insights.sub.ingest_url"`
    export INSIGHTS_TOKEN=`cat "${NUODB_CFGDIR}/insights.sub.token"`
    export NUOCA_LOGFILE="${NUODB_LOGDIR}/nuoca.log"
    export NUOCA_CONFIG_FILE="${NUOCA_HOME}/etc/nuodb_domain.yml"

    # If new Admin, then use NuoCA nuodb_nuoadmin.yml config file
    if [ "$RESPONSE" = "Startup nuoadmin" ]; then
      export NUOCA_CONFIG_FILE="${NUOCA_HOME}/etc/nuoca_nuoadmin.yml"
    fi

    echo "NuoCA Config File: ${NUOCA_CONFIG_FILE}"
    echo "Insights Subscriber ID: ${INSIGHTS_SUB_ID}"
    "${NUOCA_HOME}/bin/start_zabbix_agentd.sh"
    msg="start_insights.sh: starting NuoCA on SubID: ${INSIGHTS_SUB_ID}"
    log_msg "INFO" "$msg"
    "$PYTHONCMD" "${NUOCA_HOME}/pynuoca/nuoca.py" --mode insights -o sub_id=${INSIGHTS_SUB_ID} --collection-interval 30 "${NUOCA_CONFIG_FILE}" > "${NUODB_LOGDIR}/nuoca.output" 2>&1 &
    NUOCA_PID=$!
    echo "$NUOCA_PID" > "${NUODB_RUNDIR}/nuoca.pid"
    msg="start_insights.sh: NuoCA started, PID: ${NUOCA_PID}"
    log_msg "INFO" "$msg"
  else
    log_msg "INFO" "Skipping startup, Insights is already running."
  fi
elif [ "$RESPONSE" = "Disable" ]; then
  . "${NUOCA_HOME}/bin/disable_insights.sh"
fi
