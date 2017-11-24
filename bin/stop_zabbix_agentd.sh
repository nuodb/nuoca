#!/bin/bash

NUOCA_TOPDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
cd ${NUOCA_TOPDIR}
export ZABBIX_HOME=${NUOCA_TOPDIR}/zabbix3

echo "Stopping ${ZABBIX_HOME}/sbin/zabbix_agentd."
ps -eo pid,command|grep ${ZABBIX_HOME}/sbin/zabbix_agentd | grep -v "^[0-9]* grep" | awk '{ print $1 }' | xargs -I "{}" kill -9 {}
