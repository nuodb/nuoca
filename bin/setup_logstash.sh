#!/bin/bash

NUOCA_TOPDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
cd ${NUOCA_TOPDIR}

# Download and setup logstash.

export LOGSTASH_VERSION=5.6.4
export LOGSTASH_HOME=${NUOCA_TOPDIR}/logstash
rm -fr logstash-${LOGSTASH_VERSION}.tar.gz
rm -fr logstash
echo "Downloading logstash version: ${LOGSTASH_VERSION}"
wget -q https://artifacts.elastic.co/downloads/logstash/logstash-${LOGSTASH_VERSION}.tar.gz
echo "Untaring logstash tarball"
tar -xzf logstash-${LOGSTASH_VERSION}.tar.gz
mv logstash-${LOGSTASH_VERSION} logstash
rm -fr logstash-${LOGSTASH_VERSION}.tar.gz
