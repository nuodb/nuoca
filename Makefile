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
NUO3RDPARTY := ${HOME}/nuo3rdparty

ifdef THIRDPARTY_DIR
NUO3RDPARTY := $(THIRDPARTY_DIR)
endif

export NUOCA_ROOT=${DIR}
PYTHON_ROOT := ${NUOCA_ROOT}/python

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
	tests/dev/integration/run_tests.sh

unit-test: logstash zabbix
	(cd tests/dev && PYTHONPATH=../../src:../..:../../lib ./run_unit_tests.py)

zabbix: etc/zabbix.tgz
	${NUOCA_ROOT}/bin/setup_zabbix.sh
	${NUOCA_ROOT}/bin/start_zabbix_agentd.sh

zabbix2_2-install-debian:
	wget https://repo.zabbix.com/zabbix/2.2/ubuntu/pool/main/z/zabbix/zabbix-agent_2.2.11-1+trusty_amd64.deb
	wget https://repo.zabbix.com/zabbix/2.2/ubuntu/pool/main/z/zabbix/zabbix-get_2.2.11-1+trusty_amd64.deb
	sudo dpkg -i zabbix-agent_2.2.11-1+trusty_amd64.deb
	sudo dpkg -i zabbix-get_2.2.11-1+trusty_amd64.deb

zabbix-uninstall-debian:
	sudo dpkg -r zabbix-agent
	sudo dpkg -r zabbix-get

get-pip.py:
	wget https://bootstrap.pypa.io/get-pip.py

python: get-pip.py
	mkdir -p ${PYTHON_ROOT}
	cp -r ${NUO3RDPARTY}/common/python/x86_64-linux ${PYTHON_ROOT}
	cp -r ${NUO3RDPARTY}/common/python/bin ${PYTHON_ROOT}
	cp -r ${NUO3RDPARTY}/common/python/lib ${PYTHON_ROOT}
	cp -r ${NUO3RDPARTY}/common/python/include ${PYTHON_ROOT}
	cp -r ${NUO3RDPARTY}/common/python/share ${PYTHON_ROOT}
	ln -s ${PYTHON_ROOT}/x86_64-linux/bin/python2.7 ${PYTHON_ROOT}/bin/python2.7
	ln -s ${PYTHON_ROOT}/x86_64-linux/bin/python2.7 ${PYTHON_ROOT}/bin/python2
	ln -s ${PYTHON_ROOT}/x86_64-linux/bin/python2.7 ${PYTHON_ROOT}/bin/python
	export PATH=${PYTHON_ROOT}/bin:${PATH}
	${PYTHON_ROOT}/bin/python get-pip.py
	rm -fr ${PYTHON_ROOT}/lib/python2.7/site-packages/*
	${PYTHON_ROOT}/bin/python get-pip.py
	${PYTHON_ROOT}/bin/pip install -r requirements.txt
	find ${PYTHON_ROOT} -name '*.pyc' -print | xargs -I {} rm -f {}

