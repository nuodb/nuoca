#!/bin/sh

die () { echo "$*" ; exit 1; }

python_path=$(which python) || die "ERROR: python not found ..."

python_version=`python --version 2>&1`
case "$python_version" in
    "Python 2.7"*) break ;;
    *) die "ERROR: python version 2.7 not found." ;;
esac

pip_path=$(which pip) || die "ERROR: pip not found ..."

