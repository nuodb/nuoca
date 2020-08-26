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
echo "## Running counter"
"${NUOCA_HOME}/bin/nuoca" --collection-interval=1 --self-test "${NUOCA_HOME}/tests/dev/configs/counter.yml"
echo "## Completed counter"

# counter plugin to ElasticSearch plugin
echo "## Running ElasticSearch plugin"
"${NUOCA_HOME}/tests/etc/elastic_search/es_test_delete_index.sh"
"${NUOCA_HOME}/tests/etc/elastic_search/es_test_create_index.sh"
"${NUOCA_HOME}/bin/nuoca" --collection-interval=1 --self-test "${NUOCA_HOME}/tests/dev/configs/counter_to_elastic.yml"
"${NUOCA_HOME}/tests/etc/elastic_search/es_test_show_counts.sh"
"${NUOCA_HOME}/tests/etc/elastic_search/es_test_get_count.sh"
echo "## Running ElasticSearch plugin"

# oltpbench plugin
echo "## Running oltpbench plugin"
"${NUOCA_HOME}/tests/dev/integration/test-oltpbench-plugin.sh"
echo "## Completed oltpbench plugin"

# Zabbix plugin
echo "## Running Zabbix plugin"
"${NUOCA_HOME}/bin/nuoca" --collection-interval=1 --self-test "${NUOCA_HOME}/tests/dev/configs/zabbix_to_printer.yml"
echo "## Completed Zabbix plugin"

# NuoMonitor plugin
echo "## Running NuoMonitor plugin"
"${NUOCA_HOME}/bin/nuoca" --collection-interval=10 --self-test "${NUOCA_HOME}/tests/dev/configs/nuomonitor_to_printer.yml"
echo "## Completed NuoMonitor plugin"

# NuoMonitor plugin
echo "## Running NuoMonitor plugin"
"${NUOCA_HOME}/bin/nuoca" --collection-interval=10 --self-test "${NUOCA_HOME}/tests/dev/configs/nuoadminmonitor_to_printer.yml"
echo "## Completed NuoMonitor plugin"

# InfluxDB plugin
echo "## Running InfluxDB plugin"
"${NUOCA_HOME}/bin/nuoca" --collection-interval=10 --self-test "${NUOCA_HOME}/tests/dev/configs/nuomonitor_to_influxdb.yml"
echo "## Completed InfluxDB plugin"

# Kafka Producer Output Plugin
echo "## Running Kafka Producer Output Plugin"
"${NUOCA_HOME}/tests/dev/integration/test_kafka_producer_output_plugin.sh"
echo "## Completed Kafka Producer Output Plugin"

# Router test2
echo "## Running router_test2"
"${NUOCA_HOME}/bin/nuoca" --self-test --collection-interval=1 "${NUOCA_HOME}/tests/dev/configs/router_test2.yml"
python "${NUOCA_HOME}/tests/dev/validate_json_data.py" --nuoca_collection_json_file /tmp/nuoca.router_test2.output.json --requirements_file "${NUOCA_HOME}/tests/dev/integration/route_test2.requirements.json"
echo "## Completed router_test2"

# Router test3
echo "## Running router_test3"
"${NUOCA_HOME}/bin/nuoca" --self-test --collection-interval=1 "${NUOCA_HOME}/tests/dev/configs/router_test3.yml"
python "${NUOCA_HOME}/tests/dev/validate_json_data.py" --nuoca_collection_json_file /tmp/nuoca.router_test3.output.json --requirements_file "${NUOCA_HOME}/tests/dev/integration/route_test3.requirements.json"
echo "## Completed router_test3"

# Router test1
echo "## Running router_test1"
"${NUOCA_HOME}/bin/nuoca" --self-test "${NUOCA_HOME}/tests/dev/configs/router_test1.yml"
python "${NUOCA_HOME}/tests/dev/validate_json_data.py" --nuoca_collection_json_file /tmp/nuoca.router_test1.output.json --requirements_file "${NUOCA_HOME}/tests/dev/integration/route_test1.requirements.json"
echo "## Completed router_test1"

