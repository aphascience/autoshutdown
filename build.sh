#!/bin/bash

set -e
PY_VER=3.12

# build virtual environment
PYTHON="python${PY_VER}"; export VENV="venv-${PY_VER}"
set -eu; cd "$(cd -P -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
if ! [ -f $VENV/bin/python ]; then echo " * Creating ${VENV}" && $PYTHON -m venv $VENV; fi

# install build dependencies
$VENV/bin/python3.12 -m pip install -r requirements/build.txt

# build binaries
$VENV/bin/python3.12 -m PyInstaller autoshutdown.spec -y

# move into common distribution folder
DIST_PATH=./autoshutdown_v$(cat version.properties)
rm -rf $DIST_PATH
mkdir $DIST_PATH
mv ./dist/activate_cron/* $DIST_PATH/.
mv ./dist/auto_off/auto_off $DIST_PATH/.
cp changelog.md $DIST_PATH/.
cp version.properties $DIST_PATH/.

# cleanup
rm -rf ./dist/
rm -rf $VENV
