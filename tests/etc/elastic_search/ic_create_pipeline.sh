#!/bin/sh

set -e

CMD=${0##*/}
DIR=`cd "${0%$CMD}." && pwd`
THIS_DIR=${DIR%/*}

curl -u elastic:elasticpassword -XPUT http://localhost:9200/_ingest/pipeline/ic_pipeline?pretty -H 'Content-Type: application/json' -d @${THIS_DIR}/../../etc/elastic_search/ic_pipeline
curl -u elastic:elasticpassword -XPUT http://localhost:9200/_ingest/pipeline/ic_nuocalog_pipeline?pretty -H 'Content-Type: application/json' -d @${THIS_DIR}/../../etc/elastic_search/ic_nuocalog_pipeline
curl -u elastic:elasticpassword -XPUT http://localhost:9200/_ingest/pipeline/ic_nuoadminagentlog_pipeline?pretty -H 'Content-Type: application/json' -d @${THIS_DIR}/../../etc/elastic_search/ic_nuoadminagentlog_pipeline
curl -u elastic:elasticpassword -XPUT http://localhost:9200/_ingest/pipeline/ic_nuoadminmon_pipeline?pretty -H 'Content-Type: application/json' -d @${THIS_DIR}/../../etc/elastic_search/ic_nuoadminmon_pipeline
curl -u elastic:elasticpassword -XPUT http://localhost:9200/_ingest/pipeline/ic_nuomon_pipeline?pretty -H 'Content-Type: application/json' -d @${THIS_DIR}/../../etc/elastic_search/ic_nuomon_pipeline
curl -u elastic:elasticpassword -XPUT http://localhost:9200/_ingest/pipeline/ic_zbx_pipeline?pretty -H 'Content-Type: application/json' -d @${THIS_DIR}/../../etc/elastic_search/ic_zbx_pipeline
