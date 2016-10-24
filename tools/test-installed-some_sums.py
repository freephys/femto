#!/usr/bin/env python

from __future__ import division
import sys
from optparse import OptionParser
import some_sums

# This file is a modified version of the original numpy file:
# test-installed-numpy.py

# A simple script to test the installed version of some_sums by calling
# 'some_sums.test()'. Key features:
#   -- convenient command-line syntax
#   -- sets exit status appropriately, useful for automated test environments

# It would be better to set this up as a module in the some_sums namespace, so
# that it could be run as:
#   python -m numpy.run_tests <args>
# But, python2.4's -m switch only works with top-level modules, not modules
# that are inside packages. So, once we drop 2.4 support, maybe...
# TODO: some_sums doesn't support python 2.4

# In case we are run from the source directory, we don't want to import
# some_sums from there, we want to import the installed version:
sys.path.pop(0)

parser = OptionParser("usage: %prog [options] -- [nosetests options]")
parser.add_option("-v", "--verbose",
                  action="count", dest="verbose", default=1,
                  help="increase verbosity")
parser.add_option("--doctests",
                  action="store_true", dest="doctests", default=False,
                  help="Run doctests in module")
parser.add_option("--coverage",
                  action="store_true", dest="coverage", default=False,
                  help="report coverage requires 'coverage' module")
parser.add_option("-m", "--mode",
                  action="store", dest="mode", default="fast",
                  help="'fast', 'full', or something that could be "
                       "passed to nosetests -A [default: %default]")
(options, args) = parser.parse_args()

some_sums.bench()

result = some_sums.test(options.mode,
                        verbose=options.verbose,
                        extra_argv=args,
                        doctests=options.doctests,
                        coverage=options.coverage)

if result.wasSuccessful():
    sys.exit(0)
else:
    sys.exit(1)
