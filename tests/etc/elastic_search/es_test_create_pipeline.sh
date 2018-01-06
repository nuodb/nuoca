#!/bin/sh

# (C) Copyright NuoDB, Inc. 2017-2018
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.

set -e

CMD=${0##*/}
DIR=`cd "${0%$CMD}." && pwd`
THIS_DIR=${DIR%/*}

curl -XPUT http://localhost:9200/_ingest/pipeline/es_test_pipeline?pretty -H 'Content-Type: application/json' -d @${THIS_DIR}/../../etc/elastic_search/es_test_pipeline
