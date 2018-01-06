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

if [ ! -z $1 ]; then
  SUB_ARG="--subscriber_id $1"
fi

"$PYTHONCMD" "${NUOCA_HOME}/src/insights.py" enable $SUB_ARG

echo "If the nuoagent service is running, NuoDB Insights metrics collection"
echo "will begin at the top of the hour.  If the nuoagent service is not"
echo "running, or to start collecting immediately, you can (re)start the "
echo "nuoagent the command: "
echo " "
echo "  service nuoagent restart"
echo " "
