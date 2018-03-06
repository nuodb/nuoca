# (C) Copyright NuoDB, Inc. 2017-2018
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.

# The NuoCA Kafka Producer Output plugin test uses the NuoCA Counter input
# plugin, and sends the output for both the Kafka Producer, and the Json File
# output plugins. Kafka Connect is setup in standlone mode to act as a
# Kafka Consumer and write the payload of the Kafka message to a sink
# file.  This code compares the Json formatted file, with the Kafka sink
# file and exits non-zero if they have differences.

import json
import sys

def die(msg):
  print msg
  exit(1)

def main(json_file, kafka_sink_file):
  with open(json_file) as jfp:
    jdata = jfp.read().split("\n")
    with open(kafka_sink_file) as kfp:
      kdata = kfp.read().split("\n")
      if len(jdata) != len(kdata):
        die("Wrong length")
      for i in range(len(jdata)-1):
        jdata_dict = json.loads(jdata[i])
        kdata2=kdata[i][1:-1]
        kdata3=kdata2.split(", ")
        kdata_dict = {}
        for kd in kdata3:
          kd2=kd.split('=')
          kdata_dict[kd2[0]] = kd2[1]
        for j in jdata_dict[0]:
          if not str(jdata_dict[0][j]) == kdata_dict[j]:
            die("Failed: %s" % str(jdata_dict[0][j]))
        for k in kdata_dict:
          if not str(jdata_dict[0][k]) == kdata_dict[k]:
            die("Failed: %s" % kdata_dict[k])

# Users do not call this directly, so no elaborate argument parsing is needed.
if __name__ == '__main__':
  if len(sys.argv) != 3:
    print "Syntax error: run kafka_file_sink_compare with two arguments"
    print "  kafka_file_sink_compare.py json_file kafka_sink_file"
    die("Quit")
  main(sys.argv[1], sys.argv[2])

