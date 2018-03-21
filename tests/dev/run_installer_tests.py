#!/usr/bin/env python

# (C) Copyright NuoDB, Inc. 2017-2018
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.

# For the NuoDB Installer tests, we run a small subset of
# the NuoCA Unit Tests.

from __future__ import print_function

import os
import sys
import unittest


def main():
    test_names = ['unit.test_counter_plugin',
                  'unit.test_insights',
                  'unit.test_nuoca',
                  'unit.test_nuoca_run_function']
    suite = unittest.TestLoader().loadTestsFromNames(test_names)
    res = unittest.TextTestRunner().run(suite)
    status = 0
    if len(res.errors):
        status += 2
    if len(res.failures):
        status += 1
    return status

if __name__ == '__main__':
    sys.exit(main())
