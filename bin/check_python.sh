#!/bin/sh

python_path=$(which python)
which_python_rc=$?
if [ $which_python_rc != 0 ]; then
  echo "ERROR: python not found.  You must have python in your path."
  exit 1
fi

python_version=`python --version 2>&1`
if [[ $python_version != "Python 2.7."* ]]; then
  echo "ERROR: python version 2.7 not found."
  exit 1
fi

pip_path=$(which pip)
which_pip_rc=$?
if [ $which_pip_rc != 0 ]; then
  echo "ERROR: pip not found.  You must have python pip in your path."
  exit 1
fi

