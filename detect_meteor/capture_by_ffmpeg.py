import os
import sys

from logzero import logger


"""

ffmpeg -list_devices true -f dshow -i dummy


ffmpeg -list_options true -f dshow -i video="USB Camera"


ffmpeg  configure -encoders


ffmpeg -f dshow -i video="USB Camera" -c:v h264_qsv -q 23 -vf eq=brightness=0.1  -s 1920x1080 -r 30  -t 300 test.mp4




"""


def get_device_list():
    ret = os.popen("ffmpeg -list_devices true -f dshow -i dummy").read()
    li = []
    if 'Could not enumerate video devices':
        logger.error("video devices not found")
        return []
    for line in ret.split("\n"):
        if '[dshow' in line and 'Camera' in line:
            name = line.split('"')[1].split('"')[0]
            li.append(name)
    return li


def check_ffmpeg():
    ret = os.popen("ffmpeg -h").read()
    print("ffmpeg -h ret: " + ret)
    if len(ret) > 500:
        return True
    else:
        return False


def test_check_ffmpeg():
    
    assert check_ffmpeg() == True




