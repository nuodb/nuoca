#!/bin/sh

# (C) Copyright NuoDB, Inc. 2017-2018
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.

# The NuoCA Kafka Producer Output plugin test uses the NuoCA Counter input
# plugin, and sends the output to both the Kafka Producer, and Json File
# output plugins. Kafka Connect is setup in standlone mode to act as a
# Kafka Consumer and write the payload of the Kafka message to a sink
# file.  The kafka_file_sink_compare.py code compares the Json formatted
# file, with the Kafka sink file and exits non-zero if they have
# differences.  This script handles the setup and teardown of Kafka and
# Zookeeper.

set -e

CMD=${0##*/}
DIR=`cd "${0%$CMD}." && pwd`
THIS_DIR=${DIR%/*}

NUOCA_HOME=`cd "${THIS_DIR}/../.." && pwd`
KAFKA_HOME="$NUOCA_HOME/extern/kafka"
echo "NUOCA_HOME=$NUOCA_HOME"
echo "KAFKA_HOME=$KAFKA_HOME"

cd "${THIS_DIR}"

# Kafka Producer Output Plugin
"${NUOCA_HOME}/tests/dev/bin/setup_kafka.sh"

echo "### Start of ${KAFKA_HOME}/kafka-server.log ###"
cat "${KAFKA_HOME}/kafka-server.log"
echo "### END of ${KAFKA_HOME}/kafka-server.log ###"

"${NUOCA_HOME}/tests/dev/bin/kafka_create_topic.sh"
"${NUOCA_HOME}/tests/dev/bin/kafka_start_file_sink_consumer.sh"

echo "### Start of /tmp/kafka_connect_file_sink.log ###"
cat "/tmp/kafka_connect_file_sink.log"
echo "### END of /tmp/kafka_connect_file_sink.log ###"

echo "Testing Kafka Plugin..."
"${NUOCA_HOME}/bin/nuoca" --collection-interval=1 --self-test "${NUOCA_HOME}/tests/dev/configs/kafka_test.yml"

sleep 10

echo "### Start of /tmp/nuoca.counter.output.json ###"
cat "/tmp/nuoca.counter.output.json"
echo "### END of /tmp/nuoca.counter.output.json ###"

echo "### Start of /tmp/nuocatest.kafka.sink.txt ###"
cat "/tmp/nuocatest.kafka.sink.txt"
echo "### END of /tmp/nuocatest.kafka.sink.txt ###"

echo "Checking Kafka sink file: /tmp/nuocatest.kafka.sink.txt"
python "${NUOCA_HOME}/tests/dev/integration/kafka_file_sink_compare.py" /tmp/nuoca.counter.output.json /tmp/nuocatest.kafka.sink.txt
kafka_cmp_status=$?
"${NUOCA_HOME}/tests/dev/bin/kafka_stop_file_sink_consumer.sh"
"${NUOCA_HOME}/tests/dev/bin/kafka_delete_topic.sh"
"${NUOCA_HOME}/tests/dev/bin/cleanup_kafka.sh"
if [ $kafka_cmp_status != 0 ]; then
  echo "Kafka Test Failed"
  exit 1
else
  echo "Kafka Test Successful"
fi
