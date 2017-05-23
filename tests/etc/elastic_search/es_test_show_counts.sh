#!/bin/bash

set -e

curl -XGET http://localhost:9200/es_test/_search?pretty -d '
{
  "query": {
    "match": {
      "mpCounterPlugin.nuoca_plugin": "CounterPlugin"
    }
  }
}'