# (C) Copyright NuoDB, Inc. 2017-2018
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.
#
# This file should be _sourced_ by other scripts.

# Find the NuoCA home directory.
# If the current shell is not bash, this might not work.
# In that case, users must set NUOCA_HOME.
_nuoca_PATH=${BASH_SOURCE:+${BASH_SOURCE[0]}}
: ${_nuoca_PATH:=$0}
_nuoca_env_CMD=${_nuoca_PATH##*/}
: ${NUOCA_HOME:=$(cd "${_nuoca_PATH%$_nuoca_env_CMD}.." && pwd)}
unset _nuoca_PATH _nuoca_env_CMD

[ -f "$NUOCA_HOME/etc/nuoca_setup.sh" ] \
    || { echo "Cannot locate NUOCA_HOME"; return 1; }

. "${NUOCA_HOME}/etc/nuoca_setup.sh" || return 1
. "${NUOCA_HOME}/etc/nuoca_export.sh" || return 1
