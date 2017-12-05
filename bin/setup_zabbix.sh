#!/bin/sh

# Find the NuoCA home directory.
CMD=${0##*/}
DIR=`cd "${0%$CMD}." && pwd`
NUOCA_HOME=${DIR%/*}

cd ${NUOCA_HOME}

ZABBIX_HOME=${NUOCA_HOME}/zabbix
rm -fr ${ZABBIX_HOME}
tar -xzf ${NUOCA_HOME}/etc/zabbix.tgz
echo "Done."
