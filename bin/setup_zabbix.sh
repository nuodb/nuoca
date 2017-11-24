#!/bin/bash

NUOCA_TOPDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
cd ${NUOCA_TOPDIR}

# Untar Zabbix3
export ZABBIX_HOME=${NUOCA_TOPDIR}/zabbix3
rm -fr ${ZABBIX_HOME}
tar -xzf ${NUOCA_TOPDIR}/etc/zabbix3.tgz
