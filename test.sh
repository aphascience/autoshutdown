#!/bin/bash

set -e
PY_VER=3.12

# build virtual environment
PYTHON="python${PY_VER}"; export VENV="venv-test"
set -eu; cd "$(cd -P -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
if ! [ -f $VENV/bin/python ]; then echo " * Creating ${VENV}" && $PYTHON -m venv $VENV; fi

# install build dependencies
$VENV/bin/python3.12 -m pip install -r requirements/dev.txt

# run test
$VENV/bin/python3.12 unit_tests.py
