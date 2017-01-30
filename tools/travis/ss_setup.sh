#!/usr/bin/env bash

set -ev # exit on first error, print commands

if [ "${TEST_RUN}" = "style" ]; then
    flake8 --exclude=doc .
elif [ "${TEST_RUN}" = "sdist" ]; then
    python setup.py sdist
    ARCHIVE=`ls dist/*.tar.gz`
    pip install --verbose "${ARCHIVE[0]}"
    python "tools/test-installed-femto.py"
else
    pip install --verbose "."
    python "tools/test-installed-femto.py"
fi
