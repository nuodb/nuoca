#!/bin/bash

NUOCA_HOME="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
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
