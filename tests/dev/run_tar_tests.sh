#!/bin/sh

# (C) Copyright NuoDB, Inc. 2017-2018
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.

CMD=${0##*/}
DIR=`cd "${0%$CMD}." && pwd`
NUOCA_HOME=`cd "${DIR}/../.." && pwd`

. "${NUOCA_HOME}/etc/nuoca_setup.sh"
. "${NUOCA_HOME}/etc/nuoca_export.sh"

"${NUOCA_HOME}/bin/nuoca" --collection-interval=30 --self-test "${NUOCA_HOME}/tests/dev/configs/nuodb_domain_tar.yml"

env
"$PYTHONCMD" "${NUOCA_HOME}/tests/dev/run_tar_tests.py"