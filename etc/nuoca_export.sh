# (C) Copyright NuoDB Inc. 2017  All Rights Reserved.
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

# Only set PYTHONHOME if we are using the python
# we got from nuo3rdparty.
[ "$PYTHONHOME" ] && export PYTHONHOME

export PYTHONPATH
export NUOADMINAGENTLOGCONFIG
export NUODB_INSIGHTS_SERVICE_API
