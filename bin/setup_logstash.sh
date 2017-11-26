#!/bin/bash

NUOCA_TOPDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
cd ${NUOCA_TOPDIR}

# Setup logstash.

LOGSTASH_VERSION=5.6.4    # Same as Logstach version in NuoDB bld pkg.
LOGSTASH_HOME=${NUOCA_TOPDIR}/logstash
LOGSTASH_TARBALL_NAME=logstash-${LOGSTASH_VERSION}.tar.gz
LOGSTASH_TARBALL_PATH=${NUOCA_TOPDIR}/etc/${LOGSTASH_TARBALL_NAME}
LOGSTASH_URL=https://artifacts.elastic.co/downloads/logstash/${LOGSTASH_TARBALL_NAME}


# Download, if needed
if [ ! -f ${LOGSTASH_TARBALL_PATH} ]; then
  echo "Logstash tarball not found: ${LOGSTASH_TARBALL_PATH}"
  echo "Downloading logstash: ${LOGSTASH_VERSION}"
  curl -s -L -o ${LOGSTASH_TARBALL_PATH} ${LOGSTASH_URL} 
fi

echo "Untaring logstash tarball"
tar -xzf ${LOGSTASH_TARBALL_PATH}
rm -fr ${LOGSTASH_HOME}
mv ${NUOCA_TOPDIR}/logstash-${LOGSTASH_VERSION} ${NUOCA_TOPDIR}/logstash
