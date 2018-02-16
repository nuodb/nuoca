#!/bin/sh

set -e

CMD=${0##*/}
DIR=`cd "${0%$CMD}." && pwd`
THIS_DIR=${DIR%/*}

curl -XPOST 'http://localhost:8086/query' --data-urlencode 'q=CREATE DATABASE nuoca'
