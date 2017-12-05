if [[ -z "${LOGSTASH_HOME}" ]]; then
    export LOGSTASH_HOME="${NUOCA_HOME}/logstash"
fi
export NUODB_PORT=${NUODB_PORT:-48004}
export NUODB_DOMAIN_PASSWORD=${NUODB_DOMAIN_PASSWORD:-bird}
if [ -d "${NUOCA_HOME}/python" ]; then
  export PATH=${NUOCA_HOME}/python/bin:${PATH}
  export PYTHONHOME=${NUOCA_HOME}/python:${NUOCA_HOME}/python/x86_64-linux
fi
export PATH=${PATH}:${NUOCA_HOME}/zabbix/bin
export PYTHONPATH=${NUOCA_HOME}/src:${NUOCA_HOME}:${NUOCA_HOME}/lib
export NUOADMINAGENTLOGCONFIG=${NUOCA_HOME}/etc/logstash/nuoadminagentlog.conf
