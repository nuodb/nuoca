#!/bin/sh

# (C) Copyright NuoDB, Inc. 2017-2018
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.

# Stop the Kafka file sink consumer

# Find the NuoCA home directory.
CMD=${0##*/}
DIR=`cd "${0%$CMD}./../.." && pwd`
NUOCA_HOME=${DIR%/*}

# Get environment for external tools
. "${NUOCA_HOME}/tests/dev/bin/extern_tools.env"
KAFKA_HOME="$NUOCA_HOME/extern/${kafka_version_name}"
nuocatest_kafka_file_sink="/tmp/nuocatest.kafka.sink.txt"

# Check Kafka
echo "Checking Kafka..."
"${KAFKA_HOME}/bin/kafka-topics.sh" --list --zookeeper localhost:2181
kafka_status=$?
if [ $kafka_status != 0 ]; then
  echo "Error listing Kafka topics"
  exit 1
fi

# Stop the Kafka file sink consumer, if running
"${NUOCA_HOME}/tests/dev/bin/kafka_stop_file_sink_consumer.sh"

# Delete sink file, if it exists
if [ -f ${nuocatest_kafka_file_sink} ]; then
  echo "Deleting ${nuocatest_kafka_file_sink}..."
  rm -f ${nuocatest_kafka_file_sink}
fi

# Start the Kafka file sink consumer
echo "Starting Kafka file sink consumer..."
"${KAFKA_HOME}/bin/connect-standalone.sh" "${NUOCA_HOME}/tests/etc/kafka/connect-standalone-nuoca.properties" "${NUOCA_HOME}/tests/etc/kafka/connect-file-sink-nuoca.properties" >  /tmp/kafka_connect_file_sink.log 2>&1 &
sleep 5