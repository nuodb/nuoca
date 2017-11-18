# Testing nuoca
#
# On a local devo workstation, the nuoca integration tests depends on a
# Vagrant box which contains a copy of the nuoca source code on it.  To test
# from a local devo workstation you must first start that Vagrant box or
# remake and restart that Vagrant box to pickup nuoca code changes:
#
#   make clean
#   make integration-test-start-vm
#
# Testing on Travis-CI doesn't use a Vagrant box.  The local Travis machine
# is used for all testing.
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

DIR := ${CURDIR}
export NUOCA_ROOT=${DIR}
export LOGSTASH_HOME=${DIR}/logstash
export NUOADMINAGENTLOGCONFIG=${DIR}/etc/logstash/nuoadminagentlog.conf

clean: integration-test-clean-vm-box
	bin/stop_zabbix_agentd.sh
	find . -name '*.pyc' -exec rm -f {} +
	rm -fr logstash
	rm -fr zabbix3

continuous-test: unit-test integration-test

logstash:
	bin/setup_logstash.sh

integration-test: logstash zabbix3
	tests/dev/integration/run_tests.sh

unit-test: logstash zabbix3
	(cd tests/dev && PYTHONPATH=../../src:../..:../../lib ./run_unit_tests.py)

zabbix3: etc/zabbix3.tgz
	tar -xzf etc/zabbix3.tgz
	bin/setup_zabbix.sh
	bin/start_zabbix_agentd.sh

zabbix2_2-install-debian:
	wget https://repo.zabbix.com/zabbix/2.2/ubuntu/pool/main/z/zabbix/zabbix-agent_2.2.11-1+trusty_amd64.deb
	wget https://repo.zabbix.com/zabbix/2.2/ubuntu/pool/main/z/zabbix/zabbix-get_2.2.11-1+trusty_amd64.deb
	sudo dpkg -i zabbix-agent_2.2.11-1+trusty_amd64.deb
	sudo dpkg -i zabbix-get_2.2.11-1+trusty_amd64.deb

zabbix-uninstall-debian:
	sudo dpkg -r zabbix-agent
	sudo dpkg -r zabbix-get
