#!/bin/bash

NUOCA_TOPDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
cd ${NUOCA_TOPDIR}
export ZABBIX_HOME=${NUOCA_TOPDIR}/zabbix3

zabbix_version=$(${ZABBIX_HOME}/bin/zabbix_get -s localhost -p 10050 -k agent.version 2> /dev/null)
zabbix_rc=$?
if [ $zabbix_rc != 0 ]; then
  echo "Starting ${ZABBIX_HOME}/sbin/zabbix_agentd"
  ${ZABBIX_HOME}/sbin/zabbix_agentd
else
  echo "zabbix_agentd is already running. Running version is $zabbix_version"
fi
