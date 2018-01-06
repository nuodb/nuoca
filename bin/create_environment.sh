#!/bin/sh

# (C) Copyright NuoDB, Inc. 2017-2018
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.

# Find the NuoCA home directory.
CMD=${0##*/}
DIR=`cd "${0%$CMD}." && pwd`
NUOCA_HOME=${DIR%/*}

cd "${NUOCA_HOME}"

. bin/check_python.sh

if [ -f venv ]; then
  echo "Removing old venv..."
  rm -fr venv
fi

echo "Creating venv..."
virtualenv venv
. venv/bin/activate
pip install -r requirements.txt
echo "Done."
