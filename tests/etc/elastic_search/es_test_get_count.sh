#!/bin/sh

set -e

curl -XGET http://localhost:9200/es_test/_count?pretty -d '
{
  "query": {
    "match": {
      "mpCounterPlugin.nuoca_plugin": "CounterPlugin"
    }
  }
}'

