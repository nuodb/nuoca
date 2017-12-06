#!/bin/sh

# Find the NuoCA home directory.
CMD=${0##*/}
DIR=`cd "${0%$CMD}./../.." && pwd`
NUOCA_HOME=${DIR%/*}

zabbix_version=3.0.13
zabbix_version_name=zabbix-${zabbix_version}
zabbix_url="http://sourceforge.net/projects/zabbix/files/ZABBIX%20Latest%20Stable/${zabbix_version}/zabbix-${zabbix_version}.tar.gz/download"

ZABBIX_HOME=$NUOCA_HOME/zabbix
if [ -d $ZABBIX_HOME ]; then
  rm -fr $ZABBIX_HOME
fi
curl -s -L -o ${NUOCA_HOME}/zabbix_src.tgz ${zabbix_url}
tar -xzf ${NUOCA_HOME}/zabbix_src.tgz
(cd "${zabbix_version_name}" && ./configure --enable-agent --prefix=${NUOCA_HOME}/zabbix) > /tmp/nuoca_zabbix_configure.log 2>&1
(cd "${zabbix_version_name}" && make install-strip) > /tmp/nuoca_zabbix_install.log 2>&1

