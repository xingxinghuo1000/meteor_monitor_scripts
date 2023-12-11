set -x


# first, if PYTHON_BIN is set in .config file, we will use this path
if [ -f .config ]; then

    PYTHON_BIN=`cat .config | grep PYTHON_BIN | awk -F'"' '{print $2}'`

fi


# then, if not set in .config, we will try to find PYTHON_BIN in venv
if [[ "$PYTHON_BIN" == "" ]]; then
    if [ -f ./venv/bin/python ]; then
        PYTHON_BIN="./venv/bin/python"
    fi
fi

if [ -z $PYTHON_BIN ]; then
    echo "PYTHON_BIN not found"
    exit 1
fi

$PYTHON_BIN -m pytest detect_meteor.py util.py process_one_video.py --capture=no



