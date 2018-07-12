#!/usr/bin/env python

# (C) Copyright NuoDB, Inc. 2017-2018
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.

from __future__ import print_function

import os
import sys
import unittest


def main():
    test_dir = os.path.join(os.path.dirname('__file__'), 'tar_tests')
    suite = unittest.TestLoader().discover(test_dir, pattern="test_*.py")
    res = unittest.TextTestRunner().run(suite)
    status = 0
    if len(res.errors):
        status += 2
    if len(res.failures):
        status += 1
    return status

if __name__ == '__main__':
    sys.exit(main())