#!/bin/bash

set -e

THIS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

cd ${THIS_DIR}/../../..

NUOCA_TOPDIR="$(pwd)"

cd ${THIS_DIR}

export PYTHONPATH="${NUOCA_TOPDIR}/lib"

# counter plugin
python ${NUOCA_TOPDIR}/src/nuoca.py --config-file ${NUOCA_TOPDIR}/tests/dev/configs/counter.yml --plugin-dir ${NUOCA_TOPDIR}/tests/dev/plugins --collection-interval=1 --self-test

# counter plugin to ElasticSearch plugin
${THIS_DIR}/../../etc/elastic_search/es_test_delete_index.sh
${THIS_DIR}/../../etc/elastic_search/es_test_create_index.sh
python ${NUOCA_TOPDIR}/src/nuoca.py --config-file ${NUOCA_TOPDIR}/tests/dev/configs/counter_to_elastic.yml --plugin-dir ${NUOCA_TOPDIR}/tests/dev/plugins --collection-interval=1 --self-test
${THIS_DIR}/../../etc/elastic_search/es_test_show_counts.sh
${THIS_DIR}/../../etc/elastic_search/es_test_get_count.sh

# oltpbench plugin
${THIS_DIR}/test-oltpbench-plugin.sh

# Zabbix plugin
python ${NUOCA_TOPDIR}/src/nuoca.py --config-file ${NUOCA_TOPDIR}/tests/dev/configs/zabbix_to_printer.yml --plugin-dir ${NUOCA_TOPDIR}/tests/dev/plugins --collection-interval=1 --self-test
