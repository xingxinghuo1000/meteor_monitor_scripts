#!/bin/bash

set -x
PYTHON_BIN=`cat .config | grep PYTHON_BIN | awk -F"=" '{print $2}' | awk -F'"' '{print $2}'`


$PYTHON_BIN detect_meteor.py 2>&1 | cronolog  logs/run.%Y-%m-%d.log  &


