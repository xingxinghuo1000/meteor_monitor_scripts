set -x

PYTHON_BIN=`cat config.ini | grep PYTHON_BIN | awk -F'=' '{print $2}'`

$PYTHON_BIN -m pytest detect_meteor.py util.py process_one_video.py --capture=no



