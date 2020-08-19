#!/bin/sh

# (C) Copyright NuoDB, Inc. 2017-2019
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.

# Useful functions to be used by other scripts.  The other scripts should
# source "${NUOCA_HOME}/etc/nuoca_setup.sh" and then source this script.

die () { e=$1; shift; log_failure_msg "$*"; exit $e; }

get_property() {
    grep "^ *$1 *=" "$2" | sed "s/.*= *//"
}

getown () {
    case $1 in
        (user)  stat -c %U "$2" 2>/dev/null || stat -f %Su "$2" 2>/dev/null ;;
	(group) stat -c %G "$2" 2>/dev/null || stat -f %Sg "$2" 2>/dev/null ;;
    esac
}

get_nuodb_user_group () {
    # set NUODB_USER and NUODB_GROUP if they are not already specified
    : ${NUODB_USER:=nuodb}
    : ${NUODB_GROUP:=nuodb}
}

log_msg () {
    log_level=$1
    msg=$2
    timestamp=$(date -u)
    if [ ! -f "${NUODB_LOGDIR}/nuodb_nuoca.log" ]; then
        touch "${NUODB_LOGDIR}/nuodb_nuoca.log"
        chown "$NUODB_USER:$NUODB_GROUP" "${NUODB_LOGDIR}/nuodb_nuoca.log"
    fi
    echo "${timestamp}: ${log_level} ${msg}" >> "${NUODB_LOGDIR}/nuodb_nuoca.log"
}

log_user () {
    if [ `id -u` -eq 0 ]; then
        log_msg "INFO" "utils.sh running as user: root"
    elif [ `id -un` = "$NUODB_USER" ]; then
        log_msg "INFO" "utils.sh running as user: $NUODB_USER"
    else
        msg="Not running as 'root' or '$NUODB_USER' user."
        echo "WARNING: $msg"
        log_msg "WARNING" "$msg"
    fi
}

get_nuoagent_creds () {
    propsfile="$NUODB_HOME"/etc/default.properties
    if [ -f "$propsfile" ]; then
	user="$(get_property domainUser "$propsfile")"
	["$user" ] && export DOMAIN_USER="$user" || export DOMAIN_USER="domain"
	export DOMAIN_PASSWORD="$(get_property domainPassword "$propsfile")"
    fi
}
