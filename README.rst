==================================
The NuoDB Collection Agent (NuoCA)
==================================

.. image:: https://travis-ci.org/nuodb/nuoca.svg?branch=master
    :target: https://travis-ci.org/nuodb/nuoca
    :alt: Test Results

.. contents::

The NuoDB Collection Agent (NuoCA) is a framework for collecting time-series metrics and event data from a running system and sending it to components that can consume such data.
NuoCA makes it easy to send the collected data to File System, ElasticSearch, Rest API, InfluxDB, Kafka.

Requirements
------------

* Python -- one of the following:

  - CPython_ >= 2.7

* NuoDB -- one of the following:

  - NuoDB_ >= 3.4.0

* Python libraries:
    * aenum
    * click
    * elasticsearch
    * python-dateutil
    * PyPubSub
    * PyYaml
    * requests
    * wrapt
    * Yapsy
    * kafka-python
* Logstash 5.x, if using the NuoAdminAgentLog or Logstash plugin
* Zabbix 2.2 (or later),  If using the Zabbix plugin
* ElasticSearch 5.x, if using the ElasticSearch plugin
* InfluxDB 1.4.3, if using InfluxDB
* Zookeeper 3.4.10, if using Kafka producer
* Kafka 2.11-1.0.0, if using Kafka producer

If you haven't done so already, `Download and Install NuoDB <https://www.nuodb.com/dev-center/community-edition-download>`_.

Installation
------------

The last stable release is available on PyPI and can be installed with
``pip``::

    $ pip install pynuoca

Alternatively (e.g. if ``pip`` is not available), a tarball can be downloaded
from GitHub and installed with Setuptools::

    $ curl -L https://github.com/nuodb/nuoca/archive/master.tar.gz | tar xz
    $ cd nuoca*
    $ python setup.py install
    $ # The folder nuoca* can be safely removed now.


Resources
---------

NuoDB Documentation: Documentation_

License
-------

PyNuoCA is licensed under a `MIT License <https://github.com/nuodb/nuoca/blob/master/LICENSE>`_.

.. _Documentation: https://doc.nuodb.com/Latest/Default.htm
.. _NuoDB: https://www.nuodb.com/
.. _CPython: https://www.python.org/