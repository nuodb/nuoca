if [[ -z "${LOGSTASH_HOME}" ]]; then
    export LOGSTASH_HOME="${NUOCA_HOME}/logstash"
fi
export NUODB_PORT=${48004:-$NUODB_PORT}
export NUODB_DOMAIN_PASSWORD=${bird:-$NUODB_DOMAIN_PASSWORD}
if [ -d ${NUOCA_HOME}/python ]; then
  export PATH=${NUOCA_HOME}/python/bin:${PATH}
  export PYTHONHOME=${NUOCA_HOME}/python:${NUOCA_HOME}/python/x86_64-linux
fi
export PATH=${PATH}:${NUOCA_HOME}/zabbix/bin
export PYTHONPATH=${NUOCA_HOME}/src:${NUOCA_HOME}:${NUOCA_HOME}/lib
export NUOADMINAGENTLOGCONFIG=${NUOCA_HOME}/etc/logstash/nuoadminagentlog.conf
