#!/bin/bash

NUOCA_TOPDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
cd ${NUOCA_TOPDIR}

ZABBIX_HOME=${NUOCA_TOPDIR}/zabbix
rm -fr ${ZABBIX_HOME}
tar -xzf ${NUOCA_TOPDIR}/etc/zabbix.tgz
echo "Done."
