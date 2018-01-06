#!/bin/sh

set -e

CMD=${0##*/}
DIR=`cd "${0%$CMD}." && pwd`
THIS_DIR=${DIR%/*}

curl -u elastic:elasticpassword -XPUT http://localhost:9200/_template/ic_test?pretty -d @${THIS_DIR}/../../etc/elastic_search/ic_template
curl -u elastic:elasticpassword -XPUT http://localhost:9200/_template/ic_nuocalog_test?pretty -d @${THIS_DIR}/../../etc/elastic_search/ic_nuocalog_template
curl -u elastic:elasticpassword -XPUT http://localhost:9200/_template/ic_nuoadminagentlog_test?pretty -d @${THIS_DIR}/../../etc/elastic_search/ic_nuoadminagentlog_template
curl -u elastic:elasticpassword -XPUT http://localhost:9200/_template/ic_nuoadminmon_test?pretty -d @${THIS_DIR}/../../etc/elastic_search/ic_nuoadminmon_template
curl -u elastic:elasticpassword -XPUT http://localhost:9200/_template/ic_nuomon_test?pretty -d @${THIS_DIR}/../../etc/elastic_search/ic_nuomon_template
curl -u elastic:elasticpassword -XPUT http://localhost:9200/_template/ic_zbx_test?pretty -d @${THIS_DIR}/../../etc/elastic_search/ic_zbx_template

