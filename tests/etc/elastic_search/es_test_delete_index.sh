#!/bin/sh

set -e

curl -XDELETE http://localhost:9200/es_test?pretty

