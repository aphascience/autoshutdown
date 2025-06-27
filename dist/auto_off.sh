#!/bin/bash
set -e
PY_VER=3.12
PYTHON_SCRIPT=auto_off.py
PYTHON_DEPENDENCIES=$(dirname "$0")/../requirements/prod.txt

PYTHON="python${PY_VER}"
VENV="venv-${PY_VER}"
set -eu; cd "$(cd -P -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
if ! [ -f $VENV/bin/python ]; then echo " * Creating ${VENV}" && $PYTHON -m venv $VENV; fi
$VENV/bin/$PYTHON -m pip install -r $PYTHON_DEPENDENCIES

sudo $VENV/bin/$PYTHON $PYTHON_SCRIPT $@
