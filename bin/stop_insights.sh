#!/bin/sh

# Find the NuoCA home directory.
CMD=${0##*/}
DIR=`cd "${0%$CMD}." && pwd`
NUOCA_HOME=${DIR%/*}

. "${NUOCA_HOME}/etc/nuoca_setup.sh"
. "${NUOCA_HOME}/etc/nuoca_export.sh"

if [ -f "${NUODB_RUNDIR}/nuoca.pid" ]; then
  NUOCA_PID=`cat "${NUODB_RUNDIR}/nuoca.pid"`
  kill -SIGTERM $NUOCA_PID
  echo "Killed Insights PID: $NUOCA_PID"
  rm -f "${NUODB_RUNDIR}/nuoca.pid"
fi

