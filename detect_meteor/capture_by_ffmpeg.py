import os
import sys
import psutil
import platform
import datetime
import parse_config
from logzero import logger

cfg = parse_config.parse()


"""

ffmpeg -list_devices true -f dshow -i dummy


ffmpeg -list_options true -f dshow -i video="USB Camera"


ffmpeg  configure -encoders


ffmpeg -f dshow -i video="USB Camera" -c:v h264_qsv -q 23 -vf eq=brightness=0.1  -s 1920x1080 -r 30  -t 300 test.mp4




"""
encoder_name = None
device_name = None


def init_capture():
    global encoder_name, device_name
    encoder_name = get_support_encoders()
    assert check_ffmpeg() == True
    li = get_device_list()
    assert len(li) > 0
    device_name = li[0]

def show_video_format_support():
    assert device_name != None
    ret = os.popen('ffmpeg -list_options true -f dshow -i video="{0}" 2>&1'.format(device_name)).read()
    for line in ret.split("\n"):
        if 'fps=' in line:
            logger.info("support format: " + line)



def get_device_list():
    ret = os.popen("ffmpeg -list_devices true -f dshow -i dummy 2>&1").read()
    li = []
    if 'Could not enumerate video devices' in ret:
        logger.error("video devices not found")
        return []
    for line in ret.split("\n"):
        if 'dshow' in line and 'Camera' in line:
            logger.info("line: " + line)
            name = line.split('"')[1].split('"')[0]
            li.append(name)
    logger.info("video device list:" + str(li))
    return li


def record_one_video_file():
    assert 'CAPTURE_VIDEO_PATH' in cfg
    base_path = cfg['CAPTURE_VIDEO_PATH']
    fname = get_file_name_by_current_time()
    full_name = os.path.join(base_path, fname)
    cmd = 'ffmpeg -f dshow -i video="{0}" -c:v h264_qsv -q 23 -vf eq=brightness=0.1  -s 1920x1080 -r 30  -t 300 {1}'.format(device_name, encoder_name, full_name)
    logger.info("cmd: " + cmd)
    os.popen(cmd).read()

def check_ffmpeg():
    ret = os.popen("ffmpeg -h 2>&1").read()
    #print("ffmpeg -h ret: " + ret)
    if len(ret) > 500:
        return True
    else:
        logger.error("check ffmpeg failed, ret: " + ret)
        return False

def get_file_name_by_current_time():
    n = datetime.datetime.now()
    s = n.strftime("WIN_%Y%m%d_%H_%M_%S_Pro.mp4")
    logger.info("get file name: " + s)
    return s



def get_support_encoders():
    ret = os.popen("ffmpeg  configure -encoders 2>&1").read()
    #logger.info("encoders ret: " + ret)
    assert 'h264_qsv' in ret
    cpu_info = platform.processor()
    logger.info("CPU info :" + cpu_info)
    encoder_name = None
    if 'Intel64' in cpu_info:
        encoder_name = 'h264_qsv'
    elif "AMD" in cpu_info:
        encoder_name = 'h264_amf'
    else:
        encoder_name = 'libx264'
    logger.info("try to use encoder: " + encoder_name)
    return encoder_name


def test_check_ffmpeg():
    
    assert check_ffmpeg() == True



if __name__ == "__main__":
    init_capture()
    show_video_format_support()
    get_device_list()
    get_support_encoders()
    get_file_name_by_current_time()
