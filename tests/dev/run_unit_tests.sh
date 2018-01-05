#!/bin/sh

CMD=${0##*/}
DIR=`cd "${0%$CMD}." && pwd`
NUOCA_HOME=`cd "${DIR}/../.." && pwd`

. "${NUOCA_HOME}/etc/nuoca_setup.sh"
. "${NUOCA_HOME}/etc/nuoca_export.sh"

env
"$PYTHONCMD" "${NUOCA_HOME}/tests/dev/run_unit_tests.py"
