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
. "${NUOCA_HOME}/etc/utils.sh"

echo " "
log_msg "INFO" "Called enable_insights.sh"
get_nuodb_user_group
log_user
get_nuoagent_creds

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
  chown "$NUODB_USER:$NUODB_GROUP" "$NUODB_CFGDIR"/insights.*
  insights_sub_id=$(cat ${NUODB_CFGDIR}/insights.sub.id)
  msg="Insights enabled: Subcriber ID: ${insights_sub_id}"
  log_msg "INFO" "$msg"
  echo " "
  echo "Instructions for customers running legacy Admin (nuoagent)"
  echo "=========================================================="
  echo "If the nuoagent service is running, NuoDB Insights metrics collection"
  echo "will automatically begin within 5 minutes.  If the nuoagent service is"
  echo "not running, or to start collecting immediately, you can (re)start the"
  echo "nuoagent with the command: "
  echo " "
  echo "  \"${NUODB_HOME}/etc/nuoagent\" restart"
  echo " "
  echo "Instructions for customers running NuoDB Admin (nuoadmin)"
  echo "=========================================================="
  echo "If you are running nuoadmin with TLS enabled (which is the default)"
  echo "you must manually provision a TLS key for NuoDB Insights and copy it"
  echo "into '${NUODB_CFGDIR}/keys/nuodb_insights.pem'. NuoDB Insights metrics"
  echo "collection will automatically begin within 5 minutes."
else
  msg="enable_insights.sh: Error exit status: ${exit_status}"
  log_msg "ERROR" "$msg"
fi
