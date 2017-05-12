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

clean: integration-test-clean-vm-box
	find . -name '*.pyc' -exec rm -f {} +

continuous-test: unit-test integration-test-destroy-vms integration-test

integration-test: integration-test-start-vm
	tests/dev/integration/run_tests.sh

integration-test-destroy-vms:
	if [ -d vagrant/ubuntu14_nuoca ]; then \
		(cd vagrant/ubuntu14_nuoca && vagrant destroy -f); \
	fi
	(cd vagrant/ubuntu14 && vagrant destroy -f)

integration-test-clean-vm-box: integration-test-destroy-vms
	-vagrant box remove ubuntu14_nuoca
	if [ -d vagrant/ubuntu14_nuoca ]; then \
	  rm -fr vagrant/ubuntu14_nuoca; \
	fi
	if [ -f vagrant/ubuntu14/ubuntu14_nuoca.box ]; then \
		rm -f  vagrant/ubuntu14/ubuntu14_nuoca.box; \
	fi

# It is time consuming to construct a VM every time we want to run
# a test.  Especially when the recipe to build that VM doesn't 
# change frequently.  Instead we can build that VM once and 
# tell Vagrant to make an image from it.  And then reuse that image
# in a separate Vagrantfile.
integration-test-build-vm-box: integration-test-clean-vm-box
	(cd vagrant/ubuntu14 && vagrant up r0c0)
	ssh -i vagrant/ubuntu14/.vagrant/machines/r0c0/virtualbox/private_key vagrant@192.168.60.10 sudo apt-get clean
	(cd vagrant/ubuntu14 && vagrant package --output ubuntu14_nuoca.box r0c0)
	(cd vagrant/ubuntu14 && vagrant box add ubuntu14_nuoca ubuntu14_nuoca.box)
	(cd vagrant/ubuntu14 && vagrant destroy -f r0c0)
	(cd vagrant/ubuntu14 && rm ubuntu14_nuoca.box)
	mkdir vagrant/ubuntu14_nuoca
	cp vagrant/ubuntu14/Vagrantfile.ubuntu14_nuoca vagrant/ubuntu14_nuoca/Vagrantfile

integration-test-start-vm:
	if [ ! -d vagrant/ubuntu14_nuoca ]; then \
	  make integration-test-build-vm-box; \
	fi
	(cd vagrant/ubuntu14_nuoca; vagrant up r0c0)

unit-test:
	(cd tests/dev && PYTHONPATH=../../src:../.. ./run_unit_tests.py)


