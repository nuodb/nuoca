#!/bin/sh

# (C) Copyright NuoDB, Inc. 2017-2018
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.

set -e

curl -XGET http://localhost:9200/es_test/_search?pretty -d '
{
  "query": {
    "match": {
      "NuoCA.plugin_name": "Counter"
    }
  }
}'