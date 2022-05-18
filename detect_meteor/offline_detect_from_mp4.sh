#!/bin/bash
source /home/pi/py37env/bin/activate

d=`date "+%Y%m%d_%H%M%S"`

python offline_detect_from_mp4.py >run_$d.log 2>&1 &


