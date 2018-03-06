#!/bin/sh

# (C) Copyright NuoDB, Inc. 2017-2018
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.

# Stop Kafka and Zookeeper, and remove all traces Kafka install

# Find the NuoCA home directory.
CMD=${0##*/}
DIR=`cd "${0%$CMD}./../.." && pwd`
NUOCA_HOME=${DIR%/*}

# Get environment for external tools
. "${NUOCA_HOME}/tests/dev/bin/extern_tools.env"
KAFKA_HOME="$NUOCA_HOME/extern/${kafka_version_name}"

if [ -d "$KAFKA_HOME" ]; then
  "${KAFKA_HOME}/bin/kafka-server-stop.sh"
  "${KAFKA_HOME}/bin/zookeeper-server-stop.sh"
  sleep 5
  echo "Removing previous Kafka install..."
  rm -fr "$KAFKA_HOME"
  rm -f "$NUOCA_HOME"/extern/kafka
  rm -fr /tmp/kafka-logs /tmp/zookeeper
fi
echo "Kafka cleanup complete"
