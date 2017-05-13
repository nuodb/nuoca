#!/bin/bash

set -e

THIS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

cd ${THIS_DIR}

python ${THIS_DIR}/../../../src/nuoca.py --config-file ${THIS_DIR}/../../../tests/dev/configs/counter.yaml --plugin-dir ${THIS_DIR}/../../../tests/dev/plugins --collection-interval=1 --self-test
