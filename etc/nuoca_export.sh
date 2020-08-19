# (C) Copyright NuoDB, Inc. 2017-2018
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.
#
# This file should be _sourced_ by other scripts.

export NUODB_HOME
export NUODB_CFGDIR
export NUODB_VARDIR
export NUODB_LOGDIR
export NUODB_RUNDIR
export NUOCA_HOME
export LOGSTASH_HOME
export NUODB_PORT
export NUODB_DOMAIN_PASSWORD
export PATH

export PYTHONCMD
export PYTHONPATH
export NUOADMINAGENTLOGCONFIG

# Only export PYTHONHOME if set.
[ -z "$PYTHONHOME" ] || export PYTHONHOME
