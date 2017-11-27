#!/bin/bash

set -e

THIS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

cd ${THIS_DIR}/../../..

NUOCA_HOME="$(pwd)"

cd ${THIS_DIR}

export PYTHONPATH="${NUOCA_HOME}/lib"

# counter plugin
${NUOCA_HOME}/bin/nuoca --plugin-dir ${NUOCA_HOME}/plugins --collection-interval=1 --self-test ${NUOCA_HOME}/tests/dev/configs/counter.yml

# counter plugin to ElasticSearch plugin
${THIS_DIR}/../../etc/elastic_search/es_test_delete_index.sh
${THIS_DIR}/../../etc/elastic_search/es_test_create_index.sh
${NUOCA_HOME}/bin/nuoca --plugin-dir ${NUOCA_HOME}/plugins --collection-interval=1 --self-test ${NUOCA_HOME}/tests/dev/configs/counter_to_elastic.yml
${THIS_DIR}/../../etc/elastic_search/es_test_show_counts.sh
${THIS_DIR}/../../etc/elastic_search/es_test_get_count.sh

# oltpbench plugin
${THIS_DIR}/test-oltpbench-plugin.sh

# Zabbix plugin
${NUOCA_HOME}/bin/nuoca --plugin-dir ${NUOCA_HOME}/plugins --collection-interval=1 --self-test ${NUOCA_HOME}/tests/dev/configs/zabbix_to_printer.yml

# NuoMonitor plugin
${NUOCA_HOME}/bin/nuoca --plugin-dir ${NUOCA_HOME}/plugins --collection-interval=10 --self-test ${NUOCA_HOME}/tests/dev/configs/nuomonitor_to_printer.yml

# NuoAdminMonitor plugin
${NUOCA_HOME}/bin/nuoca --plugin-dir ${NUOCA_HOME}/plugins --collection-interval=10 --self-test ${NUOCA_HOME}/tests/dev/configs/nuoadminmonitor_to_printer.yml
