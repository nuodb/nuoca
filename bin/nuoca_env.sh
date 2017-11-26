#!/bin/bash

export NUOCA_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
export LOGSTASH_HOME=${NUOCA_ROOT}/logstash
export NUODB_AGENTPORT=48004
export NUODB_DOMAIN_PASSWORD=bird
export PATH=${NUOCA_ROOT}/python/bin:${PATH}
export PYTHONPATH=${NUOCA_ROOT}/lib
export NUOADMINAGENTLOGCONFIG=${NUOCA_ROOT}/etc/logstash/nuoadminagentlog.conf
