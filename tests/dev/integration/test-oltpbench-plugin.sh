#!/bin/bash

SELF_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
pushd $SELF_PATH >/dev/null

fake_logdir="/tmp"
fake_logname="oltpbench.out"
full_log="${fake_logdir}/${fake_logname}"
fake_cfg="tests/dev/configs/oltpbench-fake.yml"

fail() {
    echo "ERROR: $1"
    exit 1
}

start_nuoca() {
    python src/nuoca.py --config-file ${fake_cfg} --plugin-dir tests/dev/plugins --collection-interval=1 --self-test
}

bg_fake_client() {
    for x in {1..4}; {
        echo ">>>[Fake-client] Writing tps: $x, ltc: $x"
        echo "23:39:47,740 (ThreadBench.java:283) INFO  - Throughput: $x Tps
23:39:47,740 (ThreadBench.java:284) INFO  - Latency Average: $x ms" >> $full_log
        sleep 1
    }
    echo ">>>[Fake-client] Pausing write (check for duplicate metric)..."
    sleep 1
    echo ">>>[Fake-client] Exiting, wait for NuoCA to cleanup..."
}

create_config() {
    echo "---
INPUT_PLUGINS:
- OLTPBenchPlugin:
    description : Internal OLTPBench workload plugin
    log_file: $fake_logname 
    log_dir: $fake_logdir
OUTPUT_PLUGINS:
- mpPrinterPlugin:
" > ${fake_cfg}
}

touch $full_log || fail "Failed to create tmp log file. Check permissions?"
pushd ../../../ >/dev/null
echo "Creating NuoCA config for OLTPBench plugin..."
create_config || fail "Failed to create OLTPBench plugin config. Exiting."
echo "Starting background worker process..."
bg_fake_client &
start_nuoca
echo "Cleaning up temp files..."
rm $full_log
rm $fake_cfg
popd >/dev/null
echo "Finished."
popd >/dev/null
