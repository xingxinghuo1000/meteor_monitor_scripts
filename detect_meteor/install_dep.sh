set -x

PYTHON_BIN=`cat .config | grep PYTHON_BIN | awk -F"=" '{print $2}' | awk -F'"' '{print $2}'`

$PYTHON_BIN -m pip install -U pip   -i https://mirrors.aliyun.com/pypi/simple/

