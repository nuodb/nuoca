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

if [ -f "${NUODB_RUNDIR}/nuoca.pid" ]; then
  NUOCA_PID=`cat "${NUODB_RUNDIR}/nuoca.pid"`
  kill $NUOCA_PID
  count=0
  while [ $count -lt 15 ]; do
    [ "$(ps -ef | grep nuoca | awk '{print $2}')" ] || break
    (( count++ ))
    sleep 1
  done
  for x in $(ps -ef | grep nuoca | awk '{print $2}'); { kill -9 $x &> /dev/null; }
  echo "Shutdown Insights PID: $NUOCA_PID"
  rm -f "${NUODB_RUNDIR}/nuoca.pid"
  "${NUOCA_HOME}/bin/stop_zabbix_agentd.sh"
fi
