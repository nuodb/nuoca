#!/bin/sh

# (C) Copyright NuoDB, Inc. 2017-2018
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.

# Setup Kafka and startup Zookeeper and Kafka servers

# Find the NuoCA home directory.
CMD=${0##*/}
DIR=`cd "${0%$CMD}./../.." && pwd`
NUOCA_HOME=${DIR%/*}

# Get environment for external tools
. "${NUOCA_HOME}/tests/dev/bin/extern_tools.env"
KAFKA_HOME="$NUOCA_HOME/extern/${kafka_version_name}"

# Start from a clean slate.
# Cleanup existing Kafka instance, if running.
"${NUOCA_HOME}/tests/dev/bin/cleanup_kafka.sh"

# Download and untar Kafka
if [ ! -f "${NUOCA_HOME}/extern/kafka.tgz" ]; then
  echo "Downloading Kafka..."
  curl -s -L -o "${NUOCA_HOME}/extern/kafka.tgz" ${kafka_url}
  curl_status=$?
  if [ $curl_status != 0 ]; then
    echo "Error downloading ${kafka_url}"
    exit 1
  fi
fi
echo "Untarring Kafka..."
(cd "${NUOCA_HOME}/extern" && tar -xzf "${NUOCA_HOME}/extern/kafka.tgz")
ln -sf "$NUOCA_HOME/extern/${kafka_version_name}" "$NUOCA_HOME/extern/kafka"

# Start zookeeper server
echo "Starting zookeeper server..."
"${KAFKA_HOME}/bin/zookeeper-server-start.sh" "${KAFKA_HOME}/config/zookeeper.properties" > "${KAFKA_HOME}/zookeeper-server.log" 2>&1 &
server_status=$?
if [ $server_status != 0 ]; then
  echo "Error starting zookeeper server"
  exit 1
fi
sleep 5

# Check zookeeper server
echo "Checking zookeeper server..."
echo stat | nc localhost 2181
status_check=$?
if [ $server_status != 0 ]; then
  echo "Error checking status of zookeeper server"
  exit 1
fi

# Start Kafka server
"${KAFKA_HOME}/bin/kafka-server-start.sh" "${NUOCA_HOME}/tests/etc/kafka/server.properties" > "${KAFKA_HOME}/kafka-server.log" 2>&1 &
server_status=$?
if [ $server_status != 0 ]; then
  echo "Error starting Kafka server"
  exit 1
fi
sleep 5

# Check Kafka Server
echo "Checking Kafka server..."
echo dump | nc localhost 2181 | grep brokers
status_check=$?
if [ $server_status != 0 ]; then
  echo "Error checking status of Kafka server"
  exit 1
fi

echo "Kafka setup complete"
