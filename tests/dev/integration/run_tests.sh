#!/bin/sh

# (C) Copyright NuoDB, Inc. 2017-2018
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.

set -e

CMD=${0##*/}
DIR=`cd "${0%$CMD}." && pwd`
THIS_DIR=${DIR%/*}

NUOCA_HOME=`cd "${THIS_DIR}/../.." && pwd`
echo "NUOCA_HOME=$NUOCA_HOME"

cd "${THIS_DIR}"

# counter plugin
"${NUOCA_HOME}/bin/nuoca" --plugin-dir "${NUOCA_HOME}/plugins" --collection-interval=1 --self-test "${NUOCA_HOME}/tests/dev/configs/counter.yml"

# counter plugin to ElasticSearch plugin
"${NUOCA_HOME}/tests/etc/elastic_search/es_test_delete_index.sh"
"${NUOCA_HOME}/tests/etc/elastic_search/es_test_create_index.sh"
"${NUOCA_HOME}/bin/nuoca" --plugin-dir "${NUOCA_HOME}/plugins" --collection-interval=1 --self-test "${NUOCA_HOME}/tests/dev/configs/counter_to_elastic.yml"
"${NUOCA_HOME}/tests/etc/elastic_search/es_test_show_counts.sh"
"${NUOCA_HOME}/tests/etc/elastic_search/es_test_get_count.sh"

# oltpbench plugin
"${NUOCA_HOME}/tests/dev/integration/test-oltpbench-plugin.sh"

# Zabbix plugin
"${NUOCA_HOME}/bin/nuoca" --plugin-dir "${NUOCA_HOME}/plugins" --collection-interval=1 --self-test "${NUOCA_HOME}/tests/dev/configs/zabbix_to_printer.yml"

# NuoMonitor plugin
"${NUOCA_HOME}/bin/nuoca" --plugin-dir "${NUOCA_HOME}/plugins" --collection-interval=10 --self-test "${NUOCA_HOME}/tests/dev/configs/nuomonitor_to_printer.yml"

# NuoAdminMonitor plugin
"${NUOCA_HOME}/bin/nuoca" --plugin-dir "${NUOCA_HOME}/plugins" --collection-interval=10 --self-test "${NUOCA_HOME}/tests/dev/configs/nuoadminmonitor_to_printer.yml"
