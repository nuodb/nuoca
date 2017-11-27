#!/bin/bash

export NUOCA_HOME="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
export LOGSTASH_HOME=${NUOCA_HOME}/logstash
export NUODB_AGENTPORT=48004
export NUODB_DOMAIN_PASSWORD=bird
if [ -d ${NUOCA_HOME}/python ]; then
  export PATH=${NUOCA_HOME}/python/bin:${PATH}
  export PYTHONHOME=${NUOCA_HOME}/python:${NUOCA_HOME}/python/x86_64-linux
fi
export PYTHONPATH=${NUOCA_HOME}/src:${NUOCA_HOME}:${NUOCA_HOME}/lib
export NUOADMINAGENTLOGCONFIG=${NUOCA_HOME}/etc/logstash/nuoadminagentlog.conf
