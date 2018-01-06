#!/bin/sh

# (C) Copyright NuoDB, Inc. 2017-2018
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.

# Find the NuoCA home directory.
CMD=${0##*/}
DIR=`cd "${0%$CMD}." && pwd`
NUOCA_HOME=${DIR%/*}

cd "${NUOCA_HOME}"
export ZABBIX_HOME="${NUOCA_HOME}/zabbix"

zabbix_version=$("${ZABBIX_HOME}/bin/zabbix_get" -s localhost -p 10050 -k agent.version 2> /dev/null)
zabbix_rc=$?
if [ $zabbix_rc != 0 ]; then
  echo "Starting ${ZABBIX_HOME}/sbin/zabbix_agentd --config ${ZABBIX_HOME}/etc/zabbix_agentd.conf"
  "${ZABBIX_HOME}/sbin/zabbix_agentd" --config ${ZABBIX_HOME}/etc/zabbix_agentd.conf
else
  echo "zabbix_agentd is already running. Running version is $zabbix_version"
fi
