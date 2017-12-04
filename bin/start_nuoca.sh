#!/bin/bash

NUOCA_HOME="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"

source ${NUOCA_HOME}/bin/nuoca_env.sh
${NUOCA_HOME}/bin/start_zabbix_agentd.sh
python ${NUOCA_HOME}/src/nuoca.py --collection-interval 30 ${NUOCA_HOME}/etc/nuodb_domain.yml > /dev/null &
NUOCA_PID=$!
echo "$NUOCA_PID" > /var/run/nuodb/nuoca.pid



