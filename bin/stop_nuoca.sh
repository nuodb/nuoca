#!/bin/bash

# (C) Copyright NuoDB, Inc. 2017-2018
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.

NUOCA_HOME="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
source ${NUOCA_HOME}/bin/nuoca_env.sh

NUOCA_PID=`cat /var/run/nuodb/nuoca.pid`
kill -SIGTERM ${NUOCA_PID}
${NUOCA_HOME}/bin/stop_zabbix_agentd.sh


