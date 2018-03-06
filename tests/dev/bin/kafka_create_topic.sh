#!/bin/sh

# (C) Copyright NuoDB, Inc. 2017-2018
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.

# Create a Kafka topic

# Find the NuoCA home directory.
CMD=${0##*/}
DIR=`cd "${0%$CMD}./../.." && pwd`
NUOCA_HOME=${DIR%/*}

# Get environment for external tools
. "${NUOCA_HOME}/tests/dev/bin/extern_tools.env"

KAFKA_HOME="$NUOCA_HOME/extern/${kafka_version_name}"

# Delete Kafka Topic nuocatest, if it exists
"${NUOCA_HOME}/tests/dev/bin/kafka_delete_topic.sh"

# Make Kafka Topic nuocatest
echo "Creating Kafka Topic nuocatest..."
"${KAFKA_HOME}/bin/kafka-topics.sh" --create --zookeeper localhost:2181 --replication-factor 1 --partitions 1 --topic nuocatest
kafka_status=$?
if [ $kafka_status != 0 ]; then
  echo "Error creating Kafka topic"
  exit 1
fi

# Describe Kafka Topic nuocatest
echo "Describing Kafka Topic nuocatest..."
"${KAFKA_HOME}/bin/kafka-topics.sh" --describe --zookeeper localhost:2181 --topic nuocatest
kafka_status=$?
if [ $kafka_status != 0 ]; then
  echo "Error describing Kafka topic"
  exit 1
fi

echo "Successfully created Kafka topic"
