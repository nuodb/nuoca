#!/bin/sh
# (C) Copyright NuoDB, Inc. 2017  All Rights Reserved.

# (C) Copyright NuoDB, Inc. 2017-2018
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.

die () { echo "$*" ; exit 1; }

python_path=$(which "${PYTHONCMD:-python}") || die "ERROR: Python not found!"
python_version=`"$python_path" --version 2>&1`
case "$python_version" in
    "Python 2.7"*) break ;;
    *) die "ERROR: Python version 2.7 not found." ;;
esac

# Why do we need pip to run nuoca?
#pip_path=$(which pip) || die "ERROR: pip not found ..."
