#!/usr/bin/env python

# Copyright (c) 2017, NuoDB, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of NuoDB, Inc. nor the names of its contributors may
#       be used to endorse or promote products derived from this software
#       without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL NUODB, INC. BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA,
# OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
# ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from __future__ import print_function

import os
import sys
import json


def compare_values(old, new):
  if type(old) != type(new):
    return False
  if isinstance(old, basestring):
    old = old.rstrip()
  return new != old


def main():
  old_data = []
  new_data = []
  with open('/tmp/nuoca.nuoadminagentlogold.output.json') as old_file:
    for line in old_file:
      old_data.append(json.loads(line))
  with open('/tmp/nuoca.nuoadminagentlog.output.json') as new_file:
    for line in new_file:
      new_data.append(json.loads(line))
  i = 0
  for old_item in old_data:
    if i + 1 >= len(new_data):
      continue
    for old_key in old_item:
      if old_key == 'NuoAdminAgentLogOld.TimeStamp':
        continue
      if old_key == 'NuoAdminAgentLogOld.collect_timestamp':
        continue
      if old_key == 'collection_interval':
        continue
      new_key = old_key.replace('NuoAdminAgentLogOld', 'NuoAdminAgentLog')
      new_item = new_data[i+1]
      if new_key not in new_item:
        print("line: %s" % str(i))
        print("Failed Key: %s" % new_key)
        sys.exit(1)
      if compare_values(old_item[old_key], new_item[new_key]):
        print("line: %s" % str(i))
        print("Failed Value: key=%s old-value=%s new-value=%s" % (new_key, str(old_item[old_key]), str(new_item[new_key])))
        sys.exit(1)

    i = i + 1


if __name__ == '__main__':
    sys.exit(main())
