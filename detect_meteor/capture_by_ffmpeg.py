import os
import sys
import psutil
import platform
import datetime
import parse_config
from logzero import logger
import traceback
import util

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


def check_ffmpeg():
    text = os.popen("ffmpeg --help 2>&1").read()
    #print("ffmpeg output text: ", text)
    if ' version ' in text and ' Copyright ' in text:
        return True
    else:
        return False


def is_hit_sum_size_limit():
    li = os.listdir(cfg['CAPTURE_VIDEO_PATH'])
    sum = 0
    for f in li:
        full_p = os.path.join(cfg['CAPTURE_VIDEO_PATH'], f)
        if os.path.exists(full_p):
            sum += os.path.getsize(full_p)
    logger.info("current size: " + str(sum/1024/1024) + " MB")
    if sum > int(cfg['VIDEO_CAP_DIR_MAX_SIZE_BYTES']):
        logger.warn("hit max limit")
        return True
    else:
        return False


def delete_old_video():
    target_dir = cfg['CAPTURE_VIDEO_PATH']
    videos = os.listdir(target_dir)
    if len(videos) == 0:
        return
    videos = [x for x in videos if x.endswith('.mp4')]
    videos.sort()
    sum_size = sum_files_size(videos)
    print("sum size      : ", sum_size)
    print("sum size limit: ", int(cfg['VIDEO_CAP_DIR_MAX_SIZE_BYTES']))
    while sum_size > int(cfg['VIDEO_CAP_DIR_MAX_SIZE_BYTES']):
        video_path = os.path.join(target_dir, videos[0])
        print("try to remove path:" + video_path)
        util.safe_os_remove(video_path)
        done_file = video_path + '.done'
        if os.path.exists(done_file):
            util.safe_os_remove(done_file)
        lock_file = video_path + '.lock'
        if os.path.exists(lock_file):
            util.safe_os_remove(lock_file)
        analyze_file = video_path + '.analyze'
        if os.path.exists(analyze_file):
            util.safe_os_remove(analyze_file)
        time_elapse_file = video_path.replace(".mp4", "")  + '.120x.mp4'
        if os.path.exists(time_elapse_file):
            util.safe_os_remove(time_elapse_file)
        log_file = video_path +'.log'
        if os.path.exists(log_file):
            util.safe_os_remove(log_file)
        videos = os.listdir(target_dir)
        videos = [x for x in videos if x.endswith('.mp4')]
        videos.sort()
        sum_size = sum_files_size(videos)
        print("sum size      : ", sum_size)
        print("sum size limit: ", MAX_TARGET_VIDEO_SIZE)




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
    full_log_name = full_name + ".log"
    start_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cmd = 'ffmpeg -f dshow -i video="{0}" -c:v {1} -q 23 -vf eq=brightness=0.1  -s 1920x1080 -r 30  -t 300 {2} >{3} 2>&1 '.format(device_name, encoder_name, full_name, full_log_name)
    logger.info("cmd: " + cmd)
    os.popen(cmd).read()
    end_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    done_content = json.dumps({"start_cap_time": start_time, "end_cap_time": end_time}, indent=4)
    done_file = full_name + ".done"
    with open(done_file, 'w') as f1:
        f1.write(done_content)


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
