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

export NUOCA_HOME=${CURDIR}
export PYTHON_ROOT=${NUOCA_HOME}/python

zabbix_version := 3.0.13
zabbix_version_name := zabbix-$(zabbix_version)
zabbix_url := https://s3.amazonaws.com/nuohub.org/zabbix-$(zabbix_version).tar.gz

.PHONY: showenv
.PHONY: clean

showenv:
	printenv

clean:
	- bin/stop_zabbix_agentd.sh
	find . -name '*.pyc' -exec rm -f {} +
	rm -fr $(PYTHON_ROOT)
	rm -fr extern/*
	rm -f /tmp/zabbix_agentd.log
	rm -f get-pip.py
	rm -fr venv

venv: requirements.txt
	bin/create_environment.sh

continuous-test: unit-test integration-test

extern/logstash:
	bin/setup_logstash.sh

integration-test: extern/logstash extern/zabbix
	. "${NUOCA_HOME}/etc/nuoca_setup.sh" && tests/dev/integration/run_tests.sh

unit-test: extern/logstash extern/zabbix
	tests/dev/run_unit_tests.sh

installer-test:
	tests/dev/run_installer_tests.sh

extern/zabbix:
	curl -s -L -o "${NUOCA_HOME}/extern/zabbix_src.tgz" "$(zabbix_url)"
	(cd extern && tar xzf "${NUOCA_HOME}/extern/zabbix_src.tgz")
	(cd extern/${zabbix_version_name} && ./configure --enable-agent --prefix="${NUOCA_HOME}/extern/zabbix") > /tmp/nuoca_zabbix_configure.log 2>&1
	(cd extern/${zabbix_version_name} && make install-strip) > /tmp/nuoca_zabbix_install.log 2>&1

zabbix_start: extern/zabbix
	'${NUOCA_HOME}/bin/start_zabbix_agentd.sh'

install-nuodb-tar:
	'${NUOCA_HOME}/tests/dev/install_nuodb_tar.sh'

tar-test: extern/logstash extern/zabbix
	tests/dev/run_tar_tests.sh