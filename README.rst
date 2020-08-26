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

  - NuoDB_ >= 4.0, 4.1

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

Example
-------

NuoCA requires a NuoDB installation on the same Linux machine.
To acquire NuoDB for a variety of different environments please visit the `NuoDB community edition homepage <https://nuodb.com/get-community-edition>`_.

Install NuoCA::

    $ pip install pynuoca

``pip`` installs the relevant files in::

    /usr/bin/nuoca
    /usr/etc/nuoca*
    /usr/lib/python2.7/site-packages/pynuoca

Start your NuoDB database and verify that NuoDB is running via ``nuocmd``::

    $ nuocmd show domain
    server version: 4.1-2-644d1d6206, server license: Enterprise
    server time: 2020-08-26T15:11:06.709, client token: 63b87d8fb5f2a8599472befaeae6fcf07dd929b7
    Servers:
      [nuoadmin-0] localhost:48005 [last_ack = 8.53] [member = ADDED] [raft_state = ACTIVE] (LEADER, Leader=nuoadmin-0, log=0/47/47) Connected *
    Databases:
      test [state = RUNNING]
        [SM] 48414cee8a28/localhost:48007 [start_id = 0] [server_id = nuoadmin-0] [pid = 1234] [node_id = 1] [last_ack =  2.58] MONITORED:RUNNING
        [TE] 48414cee8a28/localhost:48006 [start_id = 1] [server_id = nuoadmin-0] [pid = 1230] [node_id = 2] [last_ack =  2.41] MONITORED:RUNNING

We will use a simple output plugin that will write metrics to disk.
There are many other plugins available such as: ``ElasticSearch``, ``Kafka``, ``InfluxDB`` and ``Rest``.
You can use the following file::

    $ cat /usr/etc/nuoca.yml
    NUOCA_LOGFILE: /var/log/nuodb/nuoca.log

    INPUT_PLUGINS:
    - NuoAdminNuoMon:
        description : Collection from NuoDB engines
        nuocaCollectionName: NuoMon
        client_key: ${NUOCMD_CLIENT_KEY}
        api_server: ${NUOCMD_API_SERVER}

    OUTPUT_PLUGINS:
    - File:
        filePath: /tmp/output.txt


Set the expected environmental variables.
If using TLS, ``NUOCMD_CLIENT_KEY`` has to be set to your TLS client private key. This file is usually located in ``/etc/nuodb/keys/``.
``NUOCMD_API_SERVER`` has to be set to the admin server or load balancer that you want to connect to.
If running on the same machine, use ``https://localhost:8888``.

NuoCA settings are controlled by the ``nuoca_settings.yml`` file located in ``/usr/etc``.
For most installations, the defaults are acceptable::

    $ cat /usr/etc/nuoca_settings.yml
    # Global settings for NuoCA
    #
    # Override Default Logging Level INFO,
    # with one of: DEBUG, INFO, WARNING, ERROR, CRITICAL
    # nuoca.logging.level: DEBUG
    #
    # Enable nuoca.log collection (default is false)
    # collect.nuoca.log: true
    #
    # Enable Logging of collection counts (default is false)
    # logCollectionCounts: true

You are now ready to start the NuoCA server::

    $ /usr/bin/nuoca  /usr/etc/nuoca.yml
    Using CONFIG file /usr/etc/nuoca_settings.yml
    INFO:nuoca:nuoca server init.
    INFO:nuoca:NuoCA, PID: 1716
    INFO:nuoca:plugin dir: /tmp/nuoca/plugins
    INFO:nuoca:Creating plugin: NuoAdminNuoMon
    INFO:nuoca:Plugin: NuoAdminNuoMon,  PID: 1722
    INFO:nuoca:Called to start plugin: NuoAdminNuoMon
    INFO:nuoca:NuoAdminNuoMon: plugin config: {'domain_password': '', 'nuoca_start_ts': None, 'api_server': '${NUOCMD_API_SERVER}', 'description': 'Collection from NuoDB engines', 'nuocaCollectionName': 'NuoMon', 'nuoca_collection_interval': 30, 'client_key': '${NUOCMD_CLIENT_KEY}'}
    INFO:nuoca:Creating plugin: File
    INFO:nuoca:Plugin: File,  PID: 1723
    INFO:nuoca:Called to start plugin: File
    INFO:nuoca:Starting collection interval: 1598455230000

You can now find the metrics in ``/tmp/output.txt``.

Resources
---------

NuoDB Documentation: Documentation_

License
-------

PyNuoCA is licensed under a `MIT License <https://github.com/nuodb/nuoca/blob/master/LICENSE>`_.

.. _Documentation: https://doc.nuodb.com/Latest/Default.htm
.. _NuoDB: https://www.nuodb.com/dev-center/community-edition-download
.. _CPython: https://www.python.org/