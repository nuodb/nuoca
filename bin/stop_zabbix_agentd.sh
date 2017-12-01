#!/bin/sh

# Find the NuoCA home directory.
CMD=${0##*/}
DIR=`cd "${0%$CMD}." && pwd`
NUOCA_HOME=${DIR%/*}

cd ${NUOCA_HOME}
export ZABBIX_HOME=${NUOCA_HOME}/zabbix

echo "Stopping ${ZABBIX_HOME}/sbin/zabbix_agentd."
ps -eo pid,command | sed -n "s;^ *\([0-9]*\) $ZABBIX_HOME/sbin/zabbix_agentd.*;\1;p" | xargs -I '{}' kill -9 '{}'