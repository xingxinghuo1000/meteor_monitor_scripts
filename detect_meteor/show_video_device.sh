set -x
PYTHON_BIN=`cat .config | grep PYTHON_BIN | awk -F"=" '{print $2}' | awk -F'"' '{print $2}'`

$PYTHON_BIN show_video_device.py

