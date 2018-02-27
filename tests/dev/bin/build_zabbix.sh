#!/bin/sh

# (C) Copyright NuoDB, Inc. 2017-2018
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.

# Find the NuoCA home directory.
CMD=${0##*/}
DIR=`cd "${0%$CMD}./../.." && pwd`
NUOCA_HOME=${DIR%/*}

zabbix_version=3.0.13
zabbix_version_name=zabbix-${zabbix_version}
zabbix_url="https://s3.amazonaws.com/nuohub.org/zabbix-$(zabbix_version).tar.gz"

ZABBIX_HOME="$NUOCA_HOME/zabbix"
if [ -d "$ZABBIX_HOME" ]; then
  rm -fr "$ZABBIX_HOME"
fi
curl -s -L -o "${NUOCA_HOME}/zabbix_src.tgz" ${zabbix_url}
tar -xzf "${NUOCA_HOME}/zabbix_src.tgz"
(cd "${zabbix_version_name}" && ./configure --enable-agent --prefix="${NUOCA_HOME}/zabbix") > /tmp/nuoca_zabbix_configure.log 2>&1
(cd "${zabbix_version_name}" && make install-strip) > /tmp/nuoca_zabbix_install.log 2>&1

