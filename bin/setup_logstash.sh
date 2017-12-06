#!/bin/sh

# Find the NuoCA home directory.
CMD=${0##*/}
DIR=`cd "${0%$CMD}." && pwd`
NUOCA_HOME=${DIR%/*}

cd "${NUOCA_HOME}"

# Setup logstash.

LOGSTASH_VERSION=5.6.4    # Same as Logstach version in NuoDB bld pkg.
LOGSTASH_HOME=${NUOCA_HOME}/logstash
LOGSTASH_TARBALL_NAME=logstash-${LOGSTASH_VERSION}.tar.gz
LOGSTASH_TARBALL_PATH=${NUOCA_HOME}/etc/${LOGSTASH_TARBALL_NAME}
LOGSTASH_URL=https://artifacts.elastic.co/downloads/logstash/${LOGSTASH_TARBALL_NAME}


# Download, if needed
if [ ! -f "${LOGSTASH_TARBALL_PATH}" ]; then
  echo "Logstash tarball not found: ${LOGSTASH_TARBALL_PATH}"
  echo "Downloading logstash: ${LOGSTASH_VERSION}"
  curl -s -L -o "${LOGSTASH_TARBALL_PATH}" ${LOGSTASH_URL}
fi

echo "Untaring logstash tarball"
tar -xzf "${LOGSTASH_TARBALL_PATH}"
rm -fr "${LOGSTASH_HOME}"
mv "${NUOCA_HOME}/logstash-${LOGSTASH_VERSION}" "${NUOCA_HOME}/logstash"
