#!/bin/bash

mkdir nuodb-test
tar -xzf /tmp/nuodb.tar.gz -C nuodb-test
mv nuodb-test/nuodb-* nuodb-test/nuodb
export NUODB_ROOT=nuodb-test/nuodb
export PATH=${NUODB_ROOT}/bin:${PATH}
cp "${NUODB_ROOT}/etc/default.properties.sample" "${NUODB_ROOT}/etc/default.properties"
sudo chmod 777 $NUODB_ROOT/etc/default.properties
sudo echo "domainPassword = bird" >> "${NUODB_ROOT}/etc/default.properties" 
echo "Formating system settings."
source ${NUODB_ROOT}/etc/nuodb_setup.sh
${NUODB_ROOT}/etc/nuoagent start
${NUODB_ROOT}/etc/nuorestsvc start
echo "Starting Storage Manager."
${NUODB_ROOT}/bin/nuodbmgr --broker localhost --password bird --command "start process sm host localhost database nuoca_test archive ${NUODB_ROOT}/var/opt/production-archives/nuoca_test waitForRunning true initialize true "
echo "Starting Transaction Engine."
${NUODB_ROOT}/bin/nuodbmgr --broker localhost --password bird --command "start process te host localhost database nuoca_test waitForRunning true options '--dba-user dba --dba-password dba'"