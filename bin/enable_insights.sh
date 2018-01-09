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
else
  cat <<EOF
NuoDB Insights Opt-In

You are about to enable the NuoDB Insights plug in ("Insights").  There is no
charge to enable or use Insights, and you may disable it at any time.  Insights
is part of the NuoDB Services, and except as set forth below, is subject to our
Terms of Use and Privacy Policy:

https://www.nuodb.com/privacy-policy
https://www.nuodb.com/terms-use

Insights collects anonymized data about your NuoDB implementation, and use,
including system information, configuration, response times, load averages,
usage statistics, and user activity logs ("Usage Information").  Usage
Information does not include any personally identifiable information ("PII"),
but may include some aggregated and anonymized information derived from data
that may be considered PII in some contexts (e.g., user locations or IP
addresses).

NuoDB uses Usage Information to monitor, analyze and improve the performance
and reliability of our Services, and to contribute to analytical models used by
NuoDB.  Usage Information is not shared with any third parties.  Insights also
includes a user dashboard that allows administrators to view the performance of
your NuoDB implementation.

If you agree to these terms, please type "Y" to enable Insights.  And thank you
for helping us build a better service.

EOF

  while true; do
    read -p "Do you agree? Y or N: " yn
    case $yn in
        [Yy]* ) break;;
        [Nn]* ) exit;;
        * ) echo "Please answer Y or N.";;
    esac
done
fi

echo " "
"$PYTHONCMD" "${NUOCA_HOME}/src/insights.py" enable $SUB_ARG
echo " "
echo "If the nuoagent service is running, NuoDB Insights metrics collection"
echo "will begin at the top of the hour.  If the nuoagent service is not"
echo "running, or to start collecting immediately, you can (re)start the "
echo "nuoagent with the command: "
echo " "
echo "  service nuoagent restart"
echo " "
