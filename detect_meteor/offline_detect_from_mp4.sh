#!/bin/bash


./venv/bin/python3 detect_meteor.py 2>&1 | cronolog  logs/run.%Y-%m-%d.log  &


