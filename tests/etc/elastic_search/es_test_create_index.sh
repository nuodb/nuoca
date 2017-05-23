#!/bin/bash

set -e

THIS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

curl -XPUT http://localhost:9200/es_test?pretty -d @${THIS_DIR}/es_test_mappings

