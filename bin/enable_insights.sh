#!/bin/bash

NUOCA_HOME="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"

(cd "${NUOCA_HOME}" && make -s logstash)

. "${NUOCA_HOME}/etc/nuoca_setup.sh"
. "${NUOCA_HOME}/etc/nuoca_export.sh"

if [ ! -z $1 ]; then
  SUB_ARG="--subscriber_id $1"
fi

python "${NUOCA_HOME}/src/insights.py" enable $SUB_ARG

echo "If the nuoagent & nuorestsvc service is running, NuoDB Insights metrics collection"
echo "will begin at the top of the hour.  If the nuoagent & nuorestsvc service are not"
echo "running, or to start collecting immediately, restart the nuoagent & nuorestsvc with"
echo "the commands: "
echo " "
echo "  service nuoagent restart"
echo "  service nuorestsvc restart"
echo " "
