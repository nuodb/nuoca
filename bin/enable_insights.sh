#!/bin/bash

NUOCA_HOME="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"

(cd "${NUOCA_HOME}" && make -s logstash)

. "${NUOCA_HOME}/etc/nuoca_setup.sh"
. "${NUOCA_HOME}/etc/nuoca_export.sh"

if [ ! -z $1 ]; then
  SUB_ARG="--subscriber_id $1"
fi

python "${NUOCA_HOME}/src/insights.py" enable $SUB_ARG

echo "If the nuoagent service is running, NuoDB Insights metrics collection"
echo "will begin at the top of the hour.  If the nuoagent service is not"
echo "running, or to start collecting immediately, you can (re)start the "
echo "nuoagent the command: "
echo " "
echo "  service nuoagent restart"
echo " "
