#!/bin/bash

NUOCA_HOME="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
cd ${NUOCA_HOME}
export ZABBIX_HOME=${NUOCA_HOME}/zabbix

echo "Stopping ${ZABBIX_HOME}/sbin/zabbix_agentd."
ps -eo pid,command|grep ${ZABBIX_HOME}/sbin/zabbix_agentd | grep -v "^[0-9]* grep" | awk '{ print $1 }' | xargs -I "{}" kill -9 {}
