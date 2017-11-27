#!/bin/bash

NUOCA_HOME="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
cd ${NUOCA_HOME}

ZABBIX_HOME=${NUOCA_HOME}/zabbix
rm -fr ${ZABBIX_HOME}
tar -xzf ${NUOCA_HOME}/etc/zabbix.tgz
echo "Done."
