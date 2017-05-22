#!/bin/bash
#
# Elastic stack


# Don't run this as root.

#export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64

export TOP_LEVEL_DIR=/tmp/elk
export ELASTIC_VERSION=5.1.1
export ES_HOME=${TOP_LEVEL_DIR}/elasticsearch-${ELASTIC_VERSION}
export KIBANA_VERSION=5.1.1
export KIBANA_HOME=${TOP_LEVEL_DIR}/kibana-${KIBANA_VERSION}-linux-x86_64
export LOGSTASH_VERSION=5.1.1
export LOGSTASH_HOME=${TOP_LEVEL_DIR}/logstash-${LOGSTASH_VERSION}
export FILEBEATS_VERSION=5.1.1
export FILEBEATS_HOME=${TOP_LEVEL_DIR}/filebeat-${LOGSTASH_VERSION}

sudo sysctl -w vm.max_map_count=262144

mkdir -p ${TOP_LEVEL_DIR}

# Install elasticsearch
echo "Installing ElasticSearch"
cd ${TOP_LEVEL_DIR}
tar -xzf /tmp/nuoca/elasticsearch-${ELASTIC_VERSION}.tar.gz
# Install X-Pack
#cd ${ES_HOME}
#echo "Y" | bin/elasticsearch-plugin install  x-pack


# Install Kibana
echo "Installing Kibana"
cd ${TOP_LEVEL_DIR}
tar -xzf /tmp/nuoca/kibana-${KIBANA_VERSION}-linux-x86_64.tar.gz
# Install Kibana X-Pack plugin
#cd ${KIBANA_HOME}
#bin/kibana-plugin install x-pack

# Install logstash
echo "Installing Logstash"
cd ${TOP_LEVEL_DIR}
sudo apt-get install apt-transport-https
tar -xzf /tmp/nuoca/logstash-${LOGSTASH_VERSION}.tar.gz
# logstash jmx plugin -- NOTE: can take a long time to install
#cd ${LOGSTASH_HOME}
#bin/logstash-plugin install logstash-input-jmx

# Beats: Filebeat (repeat install on all nodes that will load data)
echo "Installing Filebeats"
cd ${TOP_LEVEL_DIR}
tar -xzf /tmp/nuoca/filebeat-${FILEBEATS_VERSION}-linux-x86_64.tar.gz


# Start elasticserach daemon as the vagrant user
echo "Starting ElasticSearch"
echo 'network.host: 0.0.0.0' | tee -a ${ES_HOME}/config/elasticsearch.yml
echo 'cluster.name: vagrant_elasticsearch' | tee -a ${ES_HOME}/config/elasticsearch.yml
${ES_HOME}/bin/elasticsearch 1> /tmp/es.stdout 2> /tmp/es.stderr &


# Wait for elasticsearch to start
sleep 15

cd ${TOP_LEVEL_DIR}

# Start kibana
echo "Starting Kibana"
${KIBANA_HOME}/bin/kibana 1> /tmp/kibana.stdout 2> /tmp/kibana.stderr &

sleep 5

# Test Elastic
echo "Testing ElasticSearch"
curl --silent --show-error -XGET http://localhost:9200/

# Test Kibana
echo "Testing Kibana"
curl  --silent --show-error http://localhost:5601/

