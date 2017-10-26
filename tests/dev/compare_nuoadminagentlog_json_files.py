#!/usr/bin/env python

# (C) Copyright NuoDB, Inc. 2017  All Rights Reserved.

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
