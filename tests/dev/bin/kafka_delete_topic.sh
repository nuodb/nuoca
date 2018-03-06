#!/bin/sh

# (C) Copyright NuoDB, Inc. 2017-2018
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.

# Delete a Kafka topic

# Find the NuoCA home directory.
CMD=${0##*/}
DIR=`cd "${0%$CMD}./../.." && pwd`
NUOCA_HOME=${DIR%/*}

# Get environment for external tools
. "${NUOCA_HOME}/tests/dev/bin/extern_tools.env"
KAFKA_HOME="$NUOCA_HOME/extern/${kafka_version_name}"

# Check Kafka
echo "Checking Kafka..."
"${KAFKA_HOME}/bin/kafka-topics.sh" --list --zookeeper localhost:2181
kafka_status=$?
if [ $kafka_status != 0 ]; then
  echo "Error listing Kafka topics"
  exit 1
fi

# Delete nuocatest Kafka topic if it exists
echo "Deleting Kafka Topic nuocatest, if it exists..."
"${KAFKA_HOME}/bin/kafka-topics.sh" --if-exists --delete --zookeeper localhost:2181 --topic nuocatest
kafka_status=$?
if [ $kafka_status != 0 ]; then
  echo "Error deleting Kafaka topic nuocatest"
  exit 1
fi

"${KAFKA_HOME}/bin/zookeeper-shell.sh" localhost:2181 rmr /brokers/topics/nuocatest
shell_status=$?
if [ $shell_status != 0 ]; then
  echo "Error zookeeper rmr /brokers/topics/nuocatest"
  exit 1
fi

echo "Successfully deleted Kafka topic"
