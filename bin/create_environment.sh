#!/bin/sh

# Find the NuoCA home directory.
CMD=${0##*/}
DIR=`cd "${0%$CMD}." && pwd`
NUOCA_HOME=${DIR%/*}

cd ${NUOCA_HOME}

source bin/check_python.sh

if [ -f venv ]; then
  echo "Removing old venv..."
  rm -fr venv
fi

echo "Creating venv..."
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
echo "Done."