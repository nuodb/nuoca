#!/bin/sh

# (C) Copyright NuoDB, Inc. 2017-2018
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.

# Find the NuoCA home directory.
CMD=${0##*/}
DIR=`cd "${0%$CMD}." && pwd`
NUOCA_HOME=${DIR%/*}

cd "${NUOCA_HOME}"

# Setup logstash.

LOGSTASH_VERSION=5.6.4    # Same as Logstach version in NuoDB bld pkg.
LOGSTASH_HOME=${NUOCA_HOME}/extern/logstash
LOGSTASH_TARBALL_NAME=logstash-${LOGSTASH_VERSION}.tar.gz
LOGSTASH_TARBALL_PATH=${NUOCA_HOME}/extern/${LOGSTASH_TARBALL_NAME}
LOGSTASH_URL=https://artifacts.elastic.co/downloads/logstash/${LOGSTASH_TARBALL_NAME}


# Download, if needed
if [ ! -f "${LOGSTASH_TARBALL_PATH}" ]; then
  echo "Logstash tarball not found: ${LOGSTASH_TARBALL_PATH}"
  echo "Downloading logstash: ${LOGSTASH_VERSION}"
  curl -s -L -o "${LOGSTASH_TARBALL_PATH}" "${LOGSTASH_URL}"
fi

echo "Untaring logstash tarball"
(cd extern; tar -xzf "${LOGSTASH_TARBALL_PATH}")
rm -fr "${NUOCA_HOME}/extern/${LOGSTASH_HOME}"
mv "${NUOCA_HOME}/extern/logstash-${LOGSTASH_VERSION}" "${NUOCA_HOME}/extern/logstash"
chown -R --reference="${NUOCA_HOME}" "${NUOCA_HOME}/extern/logstash"
