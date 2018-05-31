#!/bin/sh

# (C) Copyright NuoDB, Inc. 2017-2018
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.

# Find the NuoCA home directory.
CMD=${0##*/}
DIR=`cd "${0%$CMD}." && pwd`
NUOCA_HOME=${DIR%/*}

. "${NUOCA_HOME}/etc/nuoca_setup.sh"
. "${NUOCA_HOME}/etc/nuoca_export.sh"

echo " "

# if just one argument, then it is required to be an existing
# NuoDB Insights Subscriber ID.
if [ "$#" -eq 1 ]; then
  "$PYTHONCMD" "${NUOCA_HOME}/src/insights.py" enable --subscriber-id $1
  exit_status=$?
else
  "$PYTHONCMD" "${NUOCA_HOME}/src/insights.py" enable $*
  exit_status=$?
fi

if [ "$exit_status" = "0" ]; then
  echo " "
  echo "If the nuoagent service is running, NuoDB Insights metrics collection"
  echo "will begin at the top of the hour.  If the nuoagent service is not"
  echo "running, or to start collecting immediately, you can (re)start the "
  echo "nuoagent with the command: "
  echo " "
  echo "  \"${NUODB_HOME}/etc/nuoagent\" restart"
  echo " "
fi
