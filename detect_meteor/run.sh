#!/bin/bash
set -x
# usage:
#    add this script to crontab, and run it every 5 minutes. 

d=`date "+%Y%m%d_%H%M%S"`

CNT=`ps aux| grep python | grep offline_detect_from_mp4.py| wc -l`
if [ $CNT -eq 0 ]; then
    /home/pi/py37env/bin/python  offline_detect_from_mp4.py > run.log 2>&1 &
fi


