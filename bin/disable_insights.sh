#!/bin/sh

# (C) Copyright NuoDB, Inc. 2017-2018
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.# Find the NuoCA home directory.

CMD=${0##*/}
DIR=`cd "${0%$CMD}." && pwd`
NUOCA_HOME=${DIR%/*}

. "${NUOCA_HOME}/etc/nuoca_setup.sh"
. "${NUOCA_HOME}/etc/nuoca_export.sh"

propsfile="$NUODB_HOME"/etc/default.properties
user="$(grep ^domainUser $propsfile | sed 's/.*=//')"
[ "$user" ] && export DOMAIN_USER="$user" || export DOMAIN_USER="domain"
export DOMAIN_PASSWORD="$(grep ^domainPassword $propsfile | sed 's/.*=//')"

"$PYTHONCMD" "${NUOCA_HOME}/src/insights.py" disable
