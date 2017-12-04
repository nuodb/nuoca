#!/bin/sh

set -e

CMD=${0##*/}
DIR=`cd "${0%$CMD}." && pwd`
THIS_DIR=${DIR%/*}

curl -XPUT http://localhost:9200/es_test?pretty -d @${THIS_DIR}/../../etc/elastic_search/es_mappings

