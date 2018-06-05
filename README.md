# NuoCA
The NuoDB Collection Agent (NuoCA) is a framework for collecting time-series metrics and event data from a running system and sending it to components that can consume such data. NuoCA makes it easy to send the collected data to File System, ElasticSearch, Rest API, InfluxDB, Kafka.

[![Build Status](https://travis-ci.org/nuodb/nuoca.svg?branch=master)](https://travis-ci.org/nuodb/nuoca)

## Prerequisites
The list of requirements to run NuoCA:
* Python 2.7
* Python pip
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
* NuoDB (for any of the Nuo* plugins)
* Logstash 5.x, if using the NuoAdminAgentLog or Logstash plugin
* Zabbix 2.2 (or later),  If using the Zabbix plugin
* ElasticSearch 5.x, if using the ElasticSearch plugin
* InfluxDB 1.4.3, if using InfluxDB
* Zookeeper 3.4.10, if using Kafka producer
* Kafka 2.11-1.0.0, if using Kafka producer

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.