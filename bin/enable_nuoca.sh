#!/bin/bash

# (C) Copyright NuoDB, Inc. 2017-2018
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.

export NUOCA_HOME="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
export NUODB_HOME="$( cd "$( dirname "${NUOCA_HOME}" )/.." && pwd )"

cd ${NUOCA_HOME}
source ${NUOCA_HOME}/bin/nuoca_env.sh
if [ -d ${NUOCA_HOME}/logstash ]; then
  make logstash
fi
source ${NUOCA_HOME}/bin/check_python.sh

# TODO: Call NuoDB service to get the optin JSON Web Token and store it locally
echo "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWJpZCI6ImE2OWE4YjI0LWZhMWYtNDRiZi1iYmNmLThkZWVmNzcxNjc1NCJ9.jq2GTA8he1WxQf2cnocmUYjQPRdywWadhMQiXlTYsf8" > ${NUOCA_HOME}/etc/key.jwt

# backups
timestamp=`date "+%Y-%m-%d_%H-%M-%S_%Z"`
cp -p ${NUODB_HOME}/etc/default.properties ${NUODB_HOME}/etc/default.properties.backup.$timestamp
if [ -f /opt/nuodb/etc/crontab ]; then
  cp -p ${NUODB_HOME}/etc/crontab ${NUODB_HOME}/etc/crontab.backup.$timestamp
fi

# TODO: merge "customServices = CronService" into /opt/nuodb/etc/default.properties
# Currently, the only service is the CronService, so we can get by with
# this for now.
cat ${NUODB_HOME}/etc/default.properties | grep -v "^customServices" > ${NUODB_HOME}/etc/default.properties.new
echo "customServices = CronService" >> ${NUODB_HOME}/etc/default.properties.new
chown nuodb:nuodb ${NUODB_HOME}/etc/default.properties.new
cp -p ${NUODB_HOME}/etc/default.properties.new  ${NUODB_HOME}/etc/default.properties
rm ${NUODB_HOME}/etc/default.properties.new

cp -p ${NUOCA_HOME}/etc/crontab.nuoca /opt/nuodb/etc/crontab

service nuoagent restart
service nuorestsvc restart
