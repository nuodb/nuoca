#!/bin/sh

# (C) Copyright NuoDB, Inc. 2017-2018
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.

LOGSTASH_VERSION=7.2.0    # Same as logstash version in NuoDB bld extern.

# Find the NuoCA home directory.
CMD=${0##*/}
DIR=`cd "${0%$CMD}." && pwd`
NUOCA_HOME=${DIR%/*}

die() { echo "$*" 1>&2; exit 1; }

cd "$NUOCA_HOME" || die "Can't access $NUOCA_HOME"

# Setup logstash.

LOGSTASH_ROOT="$NUOCA_HOME/extern"
mkdir -p "$LOGSTASH_ROOT"

LOGSTASH_HOME="$LOGSTASH_ROOT/logstash"

LOGSTASH_NAME="logstash-$LOGSTASH_VERSION"
LOGSTASH_PATH="$LOGSTASH_ROOT/$LOGSTASH_NAME"
LOGSTASH_TARBALL_NAME="$LOGSTASH_NAME.tar.gz"
LOGSTASH_TARBALL_PATH="$LOGSTASH_PATH.tar.gz"
LOGSTASH_URL="https://artifacts.elastic.co/downloads/logstash/$LOGSTASH_TARBALL_NAME"


# Download, if needed
if [ ! -f "$LOGSTASH_TARBALL_PATH" ]; then
  echo "Logstash tarball not found: $LOGSTASH_TARBALL_PATH"
  echo "Downloading $LOGSTASH_URL"
  if ! curl -s -L -o "$LOGSTASH_TARBALL_PATH" "$LOGSTASH_URL"; then
      rm -f "$LOGSTASH_TARBALL_PATH"
      die "Download failed.  Logstash not installed."
  fi
fi


# Extract the tarball
echo "Extracting $LOGSTASH_TARBALL_PATH"
rm -rf "$LOGSTASH_PATH"
if ! (cd "$LOGSTASH_ROOT" && tar -xzf "$LOGSTASH_TARBALL_PATH"); then
    rm -f "$LOGSTASH_TARBALL_PATH"
    die "Extract failed.  Logstash not installed."
fi

# Remove any previous install in a safe way
if [ -e "$LOGSTASH_HOME" ]; then
    rm -rf "$LOGSTASH_HOME".old
    mv "$LOGSTASH_HOME" "$LOGSTASH_HOME".old \
       || die "Failed to rename $LOGSTASH_HOME"
    rm -rf "$LOGSTASH_HOME".old || echo "Failed to remove $LOGSTASH_HOME".old
fi

mv "$LOGSTASH_PATH" "$LOGSTASH_HOME" \
   || die "Failed to rename $LOGSTASH_PATH to $LOGSTASH_HOME"

# This shouldn't be needed: this script is generally invoked by the NuoDB
# agent which runs as the NuoDB user account, not as root.
chown -R --reference="$NUOCA_HOME" "$LOGSTASH_HOME"

echo "Logstash available at $LOGSTASH_HOME"
exit 0
