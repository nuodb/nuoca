# Testing nuoca
#
# To run all nuoca tests:
#
#   make continuous-test
#
# To clean up:
#
#   make clean
#
# You can run just the unit tests with:
# 
#   make unit-test
#
# You can run just the integration tests with:
#
#   make integration-test
#

export NUOCA_HOME ?= ${CURDIR}
export PYTHON_ROOT ?= ${NUOCA_HOME}/python

zabbix_version := 3.0.13
zabbix_version_name := zabbix-$(zabbix_version)
zabbix_url := http://sourceforge.net/projects/zabbix/files/ZABBIX%20Latest%20Stable/$(zabbix_version)/zabbix-$(zabbix_version).tar.gz/download

.PHONY: showenv
.PHONY: clean

showenv:
	printenv

clean:
	- bin/stop_zabbix_agentd.sh
	find . -name '*.pyc' -exec rm -f {} +
	rm -fr $(PYTHON_ROOT)
	rm -fr logstash
	rm -fr zabbix
	rm -f /tmp/zabbix_agentd.log
	rm -f get-pip.py
	rm -fr venv

venv: requirements.txt
	bin/create_environment.sh

continuous-test: unit-test integration-test

logstash:
	bin/setup_logstash.sh

integration-test: logstash zabbix
	. ${NUOCA_HOME}/etc/nuoca_env.sh
	tests/dev/integration/run_tests.sh

unit-test: logstash zabbix
	(cd tests/dev && . ${NUOCA_HOME}/etc/nuoca_env.sh && ./run_unit_tests.py)

zabbix:
	curl -s -L -o '${NUOCA_HOME}/zabbix_src.tgz' '$(zabbix_url)'
	tar xzf '${NUOCA_HOME}/zabbix_src.tgz'
	(cd ${zabbix_version_name} && ./configure --enable-agent --prefix="${NUOCA_HOME}/zabbix") > /tmp/nuoca_zabbix_configure.log 2>&1
	(cd ${zabbix_version_name} && make install-strip) > /tmp/nuoca_zabbix_install.log 2>&1

zabbix_start: zabbix
	'${NUOCA_HOME}/bin/start_zabbix_agentd.sh'

