#!/bin/bash

set -e

THIS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

cd ${THIS_DIR}

# counter plugin
python ${THIS_DIR}/../../../src/nuoca.py --config-file ${THIS_DIR}/../../../tests/dev/configs/counter.yaml --plugin-dir ${THIS_DIR}/../../../tests/dev/plugins --collection-interval=1 --self-test

# counter plugin to ElasticSearch plugin
${THIS_DIR}/../../etc/elastic_search/es_test_delete_index.sh
${THIS_DIR}/../../etc/elastic_search/es_test_create_index.sh
python ${THIS_DIR}/../../../src/nuoca.py --config-file ${THIS_DIR}/../../../tests/dev/configs/counter_to_elastic.yaml --plugin-dir ${THIS_DIR}/../../../tests/dev/plugins --collection-interval=1 --self-test
${THIS_DIR}/../../etc/elastic_search/es_test_show_counts.sh
${THIS_DIR}/../../etc/elastic_search/es_test_get_count.sh
