# (C) Copyright NuoDB, Inc. 2017-2018
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.
#
# This file should be _sourced_ by other scripts.

NUOCA_HOME="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
. "${NUOCA_HOME}/etc/nuoca_setup.sh"
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
echo "NUODB_INSIGHTS_SERVICE_API=${NUODB_INSIGHTS_SERVICE_API}"