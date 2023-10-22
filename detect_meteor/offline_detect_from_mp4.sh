#!/bin/bash


./venv/bin/python3 offline_detect_from_mp4.py 2>&1 | cronolog  run.%Y-%m-%d.log  &


