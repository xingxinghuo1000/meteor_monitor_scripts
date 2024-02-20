import os
import sys
import platform
import time
import datetime
import json
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
platform_str = platform.platform()


def init_capture():
    global encoder_name, device_name
    encoder_name = get_support_encoders()
    assert check_ffmpeg() == True
    li = get_device_list()
    assert len(li) > 0
    device_name = li[0]
    if cfg['DEVICE_NAME'] != None and cfg['DEVICE_NAME'] != '':
        device_name = cfg['DEVICE_NAME']
    logger.info("use video device: %s", device_name)
    show_video_format_support()

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


def sum_files_size(base_dir):
    sum1 = 0
    files = os.listdir(base_dir)
    for file in files:
        full_path = os.path.join(base_dir, file)
        sum1 += os.path.getsize(full_path)
    return sum1


def delete_old_video():
    target_dir = cfg['CAPTURE_VIDEO_PATH']
    while 1:
        sum_size = sum_files_size(target_dir)
        print("sum size      : ", sum_size)
        print("sum size limit: ", int(cfg['VIDEO_CAP_DIR_MAX_SIZE_BYTES']))
        if sum_size < int(cfg['VIDEO_CAP_DIR_MAX_SIZE_BYTES']):
            break
        else:

            videos = os.listdir(target_dir)
            if len(videos) == 0:
                break
            videos = [x for x in videos if x.endswith('.mp4')]
            videos.sort()
            video_path = os.path.join(target_dir, videos[0])

            print("try to remove path:" + video_path)
            util.safe_os_remove(video_path)
            done_file = video_path + '.done'
            util.safe_os_remove(done_file)
            lock_file = video_path + '.lock'
            util.safe_os_remove(lock_file)
            analyze_file = video_path + '.analyze'
            util.safe_os_remove(analyze_file)
            time_elapse_file1 = video_path.replace(".mp4", "")  + '.120x.mp4'
            util.safe_os_remove(time_elapse_file1)
            time_elapse_file2 = video_path.replace(".mp4", "")  + '.60x.mp4'
            util.safe_os_remove(time_elapse_file2)
            log_file = video_path +'.log'
            util.safe_os_remove(log_file)


def show_video_format_support():
    assert device_name != None
    if 'Windows' in platform_str:
        po = os.popen('ffmpeg -list_options true -f dshow -i video="{0}" 2>&1'.format(device_name))
        ret = po.buffer.read().decode("utf-8")
        logger.info("show device format: %s", ret)
        for line in ret.split("\n"):
            if 'fps=' in line:
                logger.info("support format: " + line)
    if 'Linux' in platform_str:
        ret = os.popen(' ffmpeg -hide_banner -f v4l2 -list_formats all -i {0}').format(device_name).read()
        logger.info("show device format: %s", ret)



def get_device_list():
    if 'Windows' in platform_str:
        po = os.popen("ffmpeg -list_devices true -f dshow -i dummy 2>&1")
        ret = po.buffer.read().decode('utf-8')
        #logger.info("ffmpeg ret: " + ret)
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
    if 'Linux' in platform_str:
        ret = os.popen('ffmpeg -hide_banner -sources v4l2 2>&1').read()
        logger.info("ffmpeg ret: " + ret)
        li = []
        for line in ret.split('\n'):
            if '/dev/' in line:
                li.append(line.split()[0])
        return li

        


def record_one_video_file():
    assert 'CAPTURE_VIDEO_PATH' in cfg
    base_path = cfg['CAPTURE_VIDEO_PATH']
    fname = get_file_name_by_current_time()
    full_name = os.path.join(base_path, fname)
    full_log_name = full_name + ".log"
    start_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if 'Windows' in platform_str:
        cmd = 'ffmpeg -f dshow -i video="{0}" -c:v {1}  -b:v 10000k -bufsize 500000 -rtbufsize 500000 -vf eq=brightness=0.1  -s 1920x1080 -r 30  -t 300 {2} >{3} 2>&1 '.format(device_name, encoder_name, full_name, full_log_name)
    if 'Linux' in platform_str:
        cmd = 'ffmpeg -i "{0}" -c:v {1}  -b:v 20000k -bufsize 500000 -rtbufsize 500000 -vf eq=brightness=0.1 -s 1920x1080 -r 30  -t 300 {2} >{3} 2>&1 '.format(device_name, encoder_name, full_name, full_log_name)
    logger.info("cmd: " + cmd)
    os.popen(cmd).read()
    end_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    write_error_flag = 0
    # read log file, read content
    try:
        with open(full_log_name) as f1:
            content = f1.read()
            if 'Could not enumerate video devices' in content:
                logger.warn("ERROR: Could not enumerate video devices")
                write_error_flag = 1
                util.safe_os_remove(full_log_name)
                time.sleep(5)
    except:
        logger.warn(traceback.format_exc())
    if write_error_flag == 0:
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
    logger.info("encoders ret: " + ret)
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
    if cfg['ENCODER'] != '':
        encoder_name = cfg['ENCODER']
    return encoder_name


def test_check_ffmpeg():
    
    assert check_ffmpeg() == True




def cap_loop():
    while 1:
        time.sleep(5)
        if cfg['CAPTURE_VIDEO_FLAG']:
            if util.should_process_now() == False:
                logger.info("is night, should capture video")
                if True == cap.is_hit_sum_size_limit():
                    cap.delete_old_video()
                cap.record_one_video_file()
                time.sleep(1)
        else:
            logger.info("capture video flag set to 0, then skip")
            time.sleep(1)



if __name__ == "__main__":
    init_capture()
    show_video_format_support()
    get_device_list()
    get_support_encoders()
    get_file_name_by_current_time()
