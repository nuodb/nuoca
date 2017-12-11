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
    "${NUOCA_HOME}/bin/start_nuoca.sh"
  fi
fi

