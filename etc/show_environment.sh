#!/bin/sh
#
# (C) Copyright NuoDB, Inc. 2017-2018
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.

# Find the NuoCA home directory.
# This is a standalone script so we don't need BASH_SOURCE.
_nuoca_env_CMD=${0##*/}
: ${NUOCA_HOME:=$(cd "${0%$_nuoca_env_CMD}.." && pwd)}
unset _nuoca_env_CMD

[ -f "$NUOCA_HOME/etc/nuoca_setup.sh" ] \
    || { echo "Cannot locate NUOCA_HOME"; return 1; }

. "${NUOCA_HOME}/etc/nuoca_setup.sh" || return 1

echo "NUODB_HOME=${NUODB_HOME}"
echo "LOGSTASH_HOME=${LOGSTASH_HOME}"
echo "NUODB_PORT=${NUODB_PORT}"
echo "NUODB_DOMAIN_PASSWORD=${NUODB_DOMAIN_PASSWORD}"
echo "PATH=${PATH}"
echo "PYTHONHOME=${PYTHONHOME}"
echo "PYTHONPATH=${PYTHONPATH}"
echo "NUOADMINAGENTLOGCONFIG=${NUOADMINAGENTLOGCONFIG}"
echo "NUODB_CFGDIR=${NUODB_CFGDIR}"
echo "NUODB_VARDIR=${NUODB_VARDIR}"
echo "NUODB_LOGDIR=${NUODB_LOGDIR}"
echo "NUODB_RUNDIR=${NUODB_RUNDIR}"
