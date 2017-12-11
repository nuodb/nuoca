#!/bin/bash

NUOCA_HOME="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"

(cd "${NUOCA_HOME}" && make -s logstash)

. "${NUOCA_HOME}/etc/nuoca_env.sh"
. "${NUOCA_HOME}/etc/nuoca_export.sh"

"${NUOCA_HOME}/bin/start_zabbix_agentd.sh"

python "${NUOCA_HOME}/src/nuoca.py" --mode insights --collection-interval 30 "${NUOCA_HOME}/etc/nuodb_domain.yml" > /dev/null 2>&1 &
NUOCA_PID=$!
echo "$NUOCA_PID" > /var/run/nuodb/nuoca.pid



