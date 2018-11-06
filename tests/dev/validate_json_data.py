#!/usr/bin/env python

# (C) Copyright NuoDB, Inc. 2017-2018
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.

from __future__ import print_function

import click
import json

# Validate the contents of a NuoCA JSON Output file against a JSON
# formatted requirements file.
#
# Requirements JSON must contain the following elements for each
# item to validate:
#
#   field: name of the field.
#   value_operator: '>', '<', '=', '!='
#   value: <the test value>
#   cardinality_operator: '>', '<', '=', '!='
#   cardinality_value: <the expected value>
#
# Example Requirements JSON file:
#[
#  {
#    "field": "Counter.collect_timestamp",
#    "value_operator": ">",
#    "value": 0
#    "cardinality_operator": ">"
#    "cardinality_value": 0
#  },
#  {
#    "field": "NuoCA.plugin_name",
#    "value_operator": "=",
#    "value": "Counter"
#    "cardinality_operator": ">"
#    "cardinality_value": 0
#  },
#  {
#    "field": "Counter.counter",
#    "value_operator": "=",
#    "value": 1
#    "cardinality_operator": ">"
#    "cardinality_value": 0
#  },
#]


def validate_failed_msg(requirement, test_value):
  msg = "FAIL: Requirement: '%s' Actual Cardinality:'%s'" % \
        (requirement, str(test_value))
  print(msg)
  exit(1)


def validate_operation(requirement, test_value):
  value_operator = requirement['value_operator']
  expected_value = requirement['value']
  if value_operator == '>':
    return test_value > expected_value
  elif value_operator == '<':
    return test_value < expected_value
  elif value_operator == '=':
    return test_value == expected_value
  elif value_operator == '!=':
    return test_value != expected_value
  else:
    print("Error: Invalid value_operator in the data requirements %s"
          % str(requirement))
    exit(1)


def validate_requirements(data_requirements, data):
  for requirement in data_requirements:
    required_fields = ['field', 'value_operator', 'value',
                       'cardinality_operator', 'cardinality_value']
    for required_field in required_fields:
      if required_field not in requirement:
        print("Error: '%s' missing from data requirements: %s"
            % (required_field, str(requirement)))
        exit(1)
    field = requirement['field']
    expected_value = requirement['value']
    cardinality_operator = requirement['cardinality_operator']
    expected_cardinality_value = requirement['cardinality_value']

    total_count = 0
    cardinality_count = 0
    for collection in data:
      for data_item in collection:
        if field in data_item:
          test_value = data_item[field]
          total_count += 1
          if field in data_item:
            if validate_operation(requirement, test_value):
              cardinality_count += 1
    if cardinality_operator == '>':
      if not cardinality_count > expected_cardinality_value:
        validate_failed_msg(requirement, cardinality_count)
    elif cardinality_operator == '<':
      if not cardinality_count < expected_cardinality_value:
        validate_failed_msg(requirement, cardinality_count)
    elif cardinality_operator == '=':
      if not cardinality_count == expected_cardinality_value:
        validate_failed_msg(requirement, cardinality_count)
    elif cardinality_operator == '!=':
      if not cardinality_count != expected_cardinality_value:
        validate_failed_msg(requirement, cardinality_count)


def validate_data(nuoca_collection_json_file, requirements_file):
  test_data = []
  with open(requirements_file, 'r') as dr_fp:
    data_requirements = json.load(dr_fp)
  with open(nuoca_collection_json_file) as test_data_fp:
    for line in test_data_fp:
      test_data.append(json.loads(line))
  validate_requirements(data_requirements, test_data)
  print("PASS: %s" % nuoca_collection_json_file)


@click.command(help="Validate NuoCA json data file against "
                    "a requirements definition")
@click.option('--nuoca_collection_json_file', default=None,
              help='Path to NuoCA collection JSON data file')
@click.option('--requirements_file', default=None,
              help='Path to requirements file')
def validate_json_data(nuoca_collection_json_file, requirements_file):
  validate_data(nuoca_collection_json_file, requirements_file)


if __name__ == "__main__":
  validate_json_data(prog_name="validate_json_data")
