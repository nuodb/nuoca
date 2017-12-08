#!/bin/sh

# Find the NuoCA home directory.
CMD=${0##*/}
DIR=`cd "${0%$CMD}./../.." && pwd`
NUOCA_HOME=${DIR%/*}

PYTHON_ROOT=$NUOCA_HOME/python
NUO3RDPARTY=${THIRDPARTY_DIR:-$HOME/nuo3rdparty}

if [ -d $PYTHON_ROOT ]; then
  rm -fr $PYTHON_ROOT
fi

curl -s -L -o get-pip.py https://bootstrap.pypa.io/get-pip.py
mkdir -p ${PYTHON_ROOT}
cp -r ${NUO3RDPARTY}/common/python/x86_64-linux ${PYTHON_ROOT}
cp -r ${NUO3RDPARTY}/common/python/bin ${PYTHON_ROOT}
cp -r ${NUO3RDPARTY}/common/python/lib ${PYTHON_ROOT}
cp -r ${NUO3RDPARTY}/common/python/include ${PYTHON_ROOT}
cp -r ${NUO3RDPARTY}/common/python/share ${PYTHON_ROOT}
cd ${PYTHON_ROOT}/bin
ln -s ../x86_64-linux/bin/python2.7 python2.7
ln -s ../x86_64-linux/bin/python2.7 python2
ln -s ../x86_64-linux/bin/python2.7 python
cd ${NUOCA_HOME}
export PATH=${PYTHON_ROOT}/bin:${PATH}
${PYTHON_ROOT}/bin/python get-pip.py
rm -fr ${PYTHON_ROOT}/lib/python2.7/site-packages/*
${PYTHON_ROOT}/bin/python get-pip.py
${PYTHON_ROOT}/bin/pip install -r requirements.txt
find ${PYTHON_ROOT} -name '*.pyc' -print | xargs -I {} rm -f {}
rm -f get-pip.py
