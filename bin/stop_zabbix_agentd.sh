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

echo "Stopping ${ZABBIX_HOME}/sbin/zabbix_agentd."
ps -eo pid,command | sed -n "s;^ *\([0-9]*\) $ZABBIX_HOME/sbin/zabbix_agentd.*;\1;p" | xargs -I '{}' kill -9 '{}'
