#!/bin/sh
# (C) Copyright NuoDB, Inc. 2018

die () { echo "$*"; exit 1; }

# Find the NuoCA home directory.
CMD=${0##*/}
DIR=`cd "${0%$CMD}." && pwd`
case $DIR in
    (*/tests/dev/bin) NUOCA_HOME=${DIR%/tests/dev/bin} ;;
    (*) die "$DIR is not in a nuoca source repository" ;;
esac

case $1 in
    (-[h?]|--help) echo "usage: $0 [<NUODB_HOME>]"; exit 0 ;;
    ('') : no argument ;;
    (*) NUODB_HOME=$1 ;;
esac

. "$NUOCA_HOME/etc/nuoca_setup.sh"

[ -d "$NUODB_HOME/etc/nuoca" ] || die "No NuoCA installed in $NUODB_HOME"

[ "$NUOCA_HOME" = "$NUODB_HOME/etc/nuoca" ] \
    && die "$NUOCA_HOME is already in a NuoDB package"

dest=$NUODB_HOME/etc/nuoca

# Clean out the existing nuoca.  Don't delete logstash, zabbix, etc.
# Really life would be a lot simpler if all these external tools were kept in
# a single separate location, like $NUOCA_HOME/extern or something.

(
    cd "$dest" || exit 1
    rm -rf Makefile bin lib plugins requirements.txt src tests
    rm -rf etc/[!l]* etc/logstash
) || die "Failed to clean $dest!"

# Copy this nuoca into NUODB_HOME
cd "$NUOCA_HOME" || die "Cannot access $NUOCA_HOME ($dest is deleted!)"
cp -a * .gitignore .travis.yml "$dest"
