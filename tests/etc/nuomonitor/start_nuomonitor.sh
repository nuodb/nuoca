#!/bin/bash

# Example:
# start_nuomonitor.sh 'https://github.com/thebithead/nuomonitor.git' /tmp 172.19.0.16 8082

set -e


THIS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

NUOMONITOR_REPO=$1
NUOMONITOR_PATH=$2
NUODB_BROKER=$3
NUOMONITOR_PORT=$4

if [ ! -d "${NUOMONITOR_PATH}/nuomonitor" ]; then
    mkdir -p ${NUOMONITOR_PATH}
    ( cd ${NUOMONITOR_PATH} ; git clone ${NUOMONITOR_REPO} )
fi

cd ${NUOMONITOR_PATH}/nuomonitor
python nuomonitor.py -l ${NUOMONITOR_PORT} -b ${NUODB_BROKER} 2>1 > /tmp/nuomonitor.log &







