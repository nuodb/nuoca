#!/bin/sh

# (C) Copyright NuoDB, Inc. 2017-2018
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.

# Stop Kafka file consumer started by kafka_start_file_consumer.sh


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

# Look for the Kafka process with
# "kafka/connect-file-sink-nuoca.properties"
# and kill it, if found
kafka_consumer_pid=`ps -ef|grep kafka/connect-file-sink-nuoca\.properties | grep -v grep | awk '{print $2}'`
if [ $kafka_consumer_pid ]; then
  echo "Killing Kafka file sink process..."
  kill $kafka_consumer_pid
  sleep 5
fi

