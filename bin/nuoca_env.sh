#!/bin/bash

export NUOCA_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
export LOGSTASH_HOME=${NUOCA_ROOT}/logstash
export NUODB_AGENTPORT=48004
export NUODB_DOMAIN_PASSWORD=bird
export PATH=${NUOCA_ROOT}/python/bin:${PATH}
export PYTHONHOME=${NUOCA_ROOT}/python:${NUOCA_ROOT}/python/x86_64-linux
export PYTHONPATH=${NUOCA_ROOT}/src:${NUOCA_ROOT}:${NUOCA_ROOT}/lib 
export NUOADMINAGENTLOGCONFIG=${NUOCA_ROOT}/etc/logstash/nuoadminagentlog.conf
