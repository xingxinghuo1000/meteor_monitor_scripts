import sys
import os
import shutil
import time
import datetime
import logzero
logzero.logfile("default.log", maxBytes=50*1024*1024*1024, backupCount=3)
import traceback
import threading
import queue
import uuid
import socket
import json
import util
import parse_config
import store_lib
import process_one_video as pov
from suntime import Sun, SunTimeException
from logzero import logger

import capture_by_ffmpeg as cap

cfg = parse_config.parse()

queue_obj = queue.Queue()



    


def run_it():
    #read_one_video("1.mp4")
    #pov.process_one_video(os.path.join("test-T", "WIN_20220507_03_23_22_Pro.mp4"))
    #pov.process_one_video(os.path.join("test-F", "WIN_20220518_03_26_44_Pro.mp4"))
    #pov.process_one_video(os.path.join("test-F", "WIN_20220518_04_10_47_Pro.mp4"))
    pov.process_one_video(os.path.join("test-F", "WIN_20220518_02_35_56_Pro.mp4"))
    #read_one_video("meteor-20211228.mp4")
    #read_one_video("meteor-20211229.mp4")
    #read_one_video("meteor-20211231.mp4")


def process_from_queue(q):
    assert cfg['PYTHON_BIN'] != ''
    while 1:
        full_path = q.get()
        if full_path == "poison":
            # this is poison, then exit
            logger.info("thread got poison, then exit")
            break
        else:
            if not store_lib.input_path_file_exists(full_path):
                logger.info("file not exists, full_path: " + full_path)
                continue
            if store_lib.input_path_file_exists(full_path + '.lock'):
                logger.info("lock file alreay exists, then return. full_path: " + full_path)
                continue
            if store_lib.input_path_file_exists(full_path + '.analyze'):
                logger.info("analyze file already exists, then return, full_path: " + full_path)
                continue
            lock_flag = try_lock_file(full_path)
            if lock_flag == False:
                logger.info("lock file failed, then return, full_path: " + full_path)
                continue
            #pov.process_one_video(full_path)
            cmd = r'''{0} offline_detect_from_mp4.py --video_file="{1}" 2>&1 '''.format(cfg['PYTHON_BIN'], full_path)
            logger.info("run cmd: " + cmd)
            text = os.popen(cmd).read()
            logger.info("process ret: " + text)
            # write analyze file, and remove lock file
            try:
                logger.info("try to remove lock file")
                if store_lib.input_path_file_exists(full_path + '.lock'):
                    store_lib.delete_input_path_file(full_path + '.lock')
            except:
                logger.warn(traceback.format_exc())


# If process is killed, then lock file will be remained as trash
# If the old lock is not deleted, then this video file will never be processed in the future
# So in every loop, 
# we will check lock file is too old, >= 3600 seconds, if True, then delete it
def del_old_lock_files(lock_list):
    # read lock content
    for lock in lock_list:
        if store_lib.input_path_file_exists(lock):
            try:
                b1 = store_lib.read_file_from_input_path(lock)
                logger.info("b1: " + str([b1]))
                if type(b1) == type("abc"):
                    text = b1
                else:
                    text = b1.decode("utf-8")
                logger.info("lock content: " + text)
                d = json.loads(text)
                if 'createTime' in d:
                    lock_t = datetime.datetime.strptime(d['createTime'], "%Y-%m-%d %H:%M:%S")
                    logger.info("lock_t: " + str(lock_t))
                    n = datetime.datetime.now()
                    logger.info("now: " + str(n))
                    delta = n - lock_t
                    logger.info("delta.total_seconds: " + str(delta.total_seconds()))
                    if delta.total_seconds() > 1800:
                        store_lib.delete_input_path_file(lock)
            except:
                logger.warn("delete old lock file Excepttion:")
                logger.warn(traceback.format_exc())

# test case
def test_del_old_lock():
    lock_file_1_full = os.path.join(cfg['input_file_base_path'], 'test1.mp4.lock')
    lock_file_2_full = os.path.join(cfg['input_file_base_path'], 'test2.mp4.lock')
    lock_content1 = '{"createTime": "2022-07-27 21:00:00"}'
    store_lib.write_file_to_input_path(lock_file_1_full, lock_content1.encode("utf-8"))
    assert True == store_lib.input_path_file_exists(lock_file_1_full)
    lock_content2 = '{"createTime": "' + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + '"}'
    store_lib.write_file_to_input_path(lock_file_2_full, lock_content2.encode("utf-8"))
    time.sleep(1)
    del_old_lock_files([lock_file_1_full, lock_file_2_full])
    assert False == store_lib.input_path_file_exists(lock_file_1_full)
    assert True  == store_lib.input_path_file_exists(lock_file_2_full)
    store_lib.delete_input_path_file(lock_file_2_full)


def filter_by_done_file(video_list, orig_list):
    temp_list_1 = []
    for x in video_list:
        analyze_file = x + '.analyze'
        #logger.info("check analyze file is exists: " + analyze_file)
        if analyze_file not in orig_list:
            temp_list_1.append(x)
    if len(temp_list_1) == 0:
        logger.info("video list is empty after analyze filter, then return")
        return []
    temp_list_2 = []
    for x in temp_list_1:
        done_file = x + '.done'
        #logger.info("check done file is exists: " + done_file)
        if done_file in orig_list:
            temp_list_2.append(x)
    if len(temp_list_2) == 0:
        logger.info("video list is empty after done filter, then return")
        return []
    return temp_list_2

def batch_process():
    #run batch
    logger.info("start one batch process")
    orig_list = store_lib.list_input_path(cfg['input_file_base_path'])
    lock_list = [os.path.join(cfg['input_file_base_path'], x) for x in orig_list if x.endswith(".lock")]
    logger.info("lock_list: " + str(lock_list))
    del_old_lock_files(lock_list)
    video_list = [x for x in orig_list if x.endswith(".mp4") and '60x' not in x and '120x' not in x]
    if len(video_list) == 0:
        logger.info("video list is empty, then return")
        return
    video_list.sort()
    video_list = filter_by_done_file(video_list, orig_list)

    if len(video_list) == 0:
        return

    # one batch process 10 files
    if len(video_list) > 30:
        video_list = video_list[:30]
    logger.info("found video list: " + str(video_list))
    # first start processor threads
    threads = []
    for i in range(cfg['EXECUTOR_NUM']):
        t = threading.Thread(target=process_from_queue, args=(queue_obj,))
        t.daemon = True
        t.start()
        threads.append(t)
    # get video list,  put them to queue
    for video_file in video_list:
        full_path = os.path.join(cfg['input_file_base_path'], video_file)
        queue_obj.put(full_path)
    # generate poison for each thread
    for i in range(cfg['EXECUTOR_NUM']):
        queue_obj.put("poison")
    # wait thread to exit
    for t in threads:
        t.join()
    logger.info("all thread exited")
                                    

def try_lock_file(full_path):
    assert cfg['LOCK_STR'] != ''
    assert cfg['IP_ADDR'] != ''
    lockfile = full_path + ".lock"
    if store_lib.input_path_file_exists(lockfile):
        return False
    else:
        try:
            d = {
                "createTime": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                "IP": cfg['IP_ADDR'],
                "LOCK_STR": cfg['LOCK_STR']
            }
            lock_content = json.dumps(d)
            store_lib.write_file_to_input_path(lockfile, lock_content.encode("utf-8"))
        except:
            logger.warn(traceback.format_exc())
            return False
        if not store_lib.input_path_file_exists(lockfile):
            # write failed, maybe file path can not be written, return False
            return False
        else:
            str_read = ""
            try:
                temp_bytes = store_lib.read_file_from_input_path(lockfile)
                if type(temp_bytes) == type("abc"):
                    str_read = temp_bytes
                else:
                    str_read = temp_bytes.decode("utf-8")
                str_read = str_read.strip("\r\n").strip()
            except:
                logger.warn(traceback.format_exc())
                return False
            if cfg['LOCK_STR'] not in str_read:
                # may be written again be other process or other machine
                return False
            else:
                # !!!!!! SUCCESS lock this file
                return True

def test_lock():
    # test 1
    if store_lib.input_path_file_exists("1.txt.lock"):
        store_lib.delete_input_path_file('1.txt.lock')
    full_path = "1.txt"
    assert True == try_lock_file("1.txt")
    if store_lib.input_path_file_exists("1.txt.lock"):
        store_lib.delete_input_path_file("1.txt.lock")
    # test 2
    if store_lib.input_path_file_exists("2.txt.lock"):
        store_lib.delete_input_path_file('2.txt.lock')
    store_lib.write_file_to_input_path("2.txt.lock", b'1123123')
    assert False == try_lock_file("2.txt")
    if store_lib.input_path_file_exists("2.txt.lock"):
        store_lib.delete_input_path_file("2.txt.lock")


def get_sun_time(latitude, longitude):
    assert type(latitude) == type(1.1)
    assert type(longitude) == type(1.1)
    sun = Sun(latitude, longitude)
    today_sr_utc = sun.get_sunrise_time()
    today_ss_utc = sun.get_sunset_time()
    today_sr_local = utc2local(today_sr_utc)
    today_ss_local = utc2local(today_ss_utc)
    logger.info("today_sr_utc: " + str(today_sr_utc))
    logger.info("today_ss_utc: " + str(today_ss_utc))
    logger.info("today_sr_local: " + str(today_sr_local))
    logger.info("today_ss_local: " + str(today_ss_local))
    return today_sr_utc, today_ss_utc, today_sr_local, today_ss_local


def should_process_now():
    n = datetime.datetime.now()
    n_str = n.strftime("%H:%M")
    delta2h = datetime.timedelta(hours=2)
    sr_utc, ss_utc, sr_local, ss_local = get_sun_time(float(cfg["LATITUDE"]), 
            float(cfg['LONGITUDE']))
    black_time_sr = sr_local - delta2h
    black_time_ss = ss_local + delta2h
    a = black_time_sr.strftime("%H:%M")
    b = black_time_ss.strftime("%H:%M")
    logger.info("now: " + n_str)
    logger.info("a: " + a + "     b: " + b)
    is_ni = is_night(n_str, a, b)
    if is_ni:
        return False
    else:
        # is in daylight
        return True
    

def is_night(n_str, a, b):
    if n_str >= "00:00" and n_str < a:
        return True
    if n_str > a and n_str < b:
        return False
    if n_str >= b and n_str <= "23:59":
        return True
    return False

def test_is_night():
    assert True == is_night("00:00", "05:00", "20:00")
    assert True == is_night("00:01", "05:00", "20:00")
    assert True == is_night("04:59", "05:00", "20:00")
    assert False == is_night("05:00", "05:00", "20:00")
    assert False == is_night("05:01", "05:00", "20:00")
    assert False == is_night("07:00", "05:00", "20:00")
    assert False == is_night("12:00", "05:00", "20:00")
    assert False == is_night("15:00", "05:00", "20:00")
    assert False == is_night("19:59", "05:00", "20:00")
    assert True == is_night("20:00", "05:00", "20:00")
    assert True == is_night("20:01", "05:00", "20:00")
    assert True == is_night("22:01", "05:00", "20:00")
    assert True == is_night("23:59", "05:00", "20:00")

    
def utc2local(utc_dtm):
    local_tm = datetime.datetime.fromtimestamp( 0 )
    utc_tm = datetime.datetime.utcfromtimestamp( 0 )
    offset = local_tm - utc_tm
    return utc_dtm + offset

def local2utc(local_dtm):
    return datetime.datetime.utcfromtimestamp( local_dtm.timestamp() )


def clean_temp_dir():
    cur_time = time.time()
    if os.path.exists("temp"):
        logger.info("try to clean temp dir")
        for f in os.listdir("temp"):
            ff = os.path.join("temp", f)
            t = os.path.getmtime(ff)
            diff = int(cur_time - t)
            logger.info("(current time) - (temp time create time) = " + str(diff))
            if diff > 7200:
                logger.info("try to remove temp file: "+f)
                util.safe_os_remove(ff)




if __name__ == "__main__":
    assert True == cap.check_ffmpeg()
    clean_temp_dir()
    if '--debug' in sys.argv:
        cfg['DEBUG'] = 1
    for arg in sys.argv:
        if '--video-file=' in arg:
            arg = arg.replace("--video-file=", "--video_file=")
        if '--video_file=' in arg:
            logger.info("process single video file")
            full_path = arg.split("--video_file=")[1]
            if full_path.startswith('"'):
                full_path = full_path.strip('"')
            store_lib.input_path_file_exists(full_path)
            logger.info("full_path: "+full_path)
            pov.process_one_video(full_path)
            sys.exit(0)
        if '--run_it' in arg:
            cfg['DEBUG'] = 1
            run_it()
            sys.exit(0)

    # loop process or capture video
    cap.init_capture()
    while 1:
        if should_process_now():
            logger.info("sould process get True, process begin")
            try:
                batch_process()
            except:
                logger.warn("Error when batch_process")
                logger.warn(traceback.format_exc())
            logger.info("after process, sleep 60")
            time.sleep(60)
        else:
            logger.info("is night, should capture video")
            if True == cap.is_hit_sum_size_limit():
                cap.delete_old_video()
            cap.record_one_video_file()
            time.sleep(1)

