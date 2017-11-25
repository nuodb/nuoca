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
export NUOCA_ROOT=${DIR}
export LOGSTASH_HOME=${DIR}/logstash
export NUOADMINAGENTLOGCONFIG=${DIR}/etc/logstash/nuoadminagentlog.conf
export PYTHON_DEST=${NUOCA_ROOT}/python_x86_64-linux
export PYTHON_DEST_TGZ=${NUOCA_ROOT}/etc/python_x86_64-linux.tgz

clean:
	- bin/stop_zabbix_agentd.sh
	find . -name '*.pyc' -exec rm -f {} +
	rm -fr ${PYTHON_DEST} ${PYTHON_DEST_TGZ}
	rm -fr logstash
	rm -fr zabbix3
	rm -f /tmp/zabbix_agentd.log
	rm -f get-pip.py
	rm -fr venv

venv: requirements.txt
	bin/create_environment.sh

continuous-test: unit-test integration-test

logstash:
	bin/setup_logstash.sh

integration-test: logstash zabbix3
	tests/dev/integration/run_tests.sh

unit-test: logstash zabbix3
	(cd tests/dev && PYTHONPATH=../../src:../..:../../lib ./run_unit_tests.py)

zabbix3: etc/zabbix3.tgz
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

python_x86_64-linux: get-pip.py
	mkdir -p ${PYTHON_DEST}
	cp -r ${NUO3RDPARTY}/common/python/x86_64-linux ${PYTHON_DEST}
	cp -r ${NUO3RDPARTY}/common/python/bin ${PYTHON_DEST}
	cp -r ${NUO3RDPARTY}/common/python/lib ${PYTHON_DEST}
	cp -r ${NUO3RDPARTY}/common/python/include ${PYTHON_DEST}
	cp -r ${NUO3RDPARTY}/common/python/share ${PYTHON_DEST}
	ln -s ../x86_64-linux/bin/python2.7 python_x86_64-linux/bin/python2.7
	ln -s ../x86_64-linux/bin/python2.7 python_x86_64-linux/bin/python2
	ln -s ../x86_64-linux/bin/python2.7 python_x86_64-linux/bin/python
	export PATH=${PYTHON_DEST}/bin:${PATH}
	${PYTHON_DEST}/bin/python get-pip.py
	rm -fr ${PYTHON_DEST}/lib/python2.7/site-packages/*
	${PYTHON_DEST}/bin/python get-pip.py
	${PYTHON_DEST}/bin/pip install -r requirements.txt
	find ${PYTHON_DEST} -name '*.pyc' -print | xargs -I {} rm -f {}
	tar -czf ${PYTHON_DEST_TGZ} python_x86_64-linux
