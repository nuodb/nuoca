#!/bin/sh

# (C) Copyright NuoDB, Inc. 2017-2018
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.# Find the NuoCA home directory.

# Find the NuoCA home directory.
CMD=${0##*/}
DIR=`cd "${0%$CMD}." && pwd`
NUOCA_HOME=${DIR%/*}

. "${NUOCA_HOME}/etc/nuoca_setup.sh"
. "${NUOCA_HOME}/etc/nuoca_export.sh"
. "${NUOCA_HOME}/etc/utils.sh"

echo " "
log_msg "INFO" "Called disable_insights.sh"
get_nuodb_user_group
log_user
get_nuoagent_creds

"$PYTHONCMD" "${NUOCA_HOME}/src/insights.py" disable

"${NUOCA_HOME}/bin/stop_insights.sh"
log_msg "INFO" "Insights is disabled."