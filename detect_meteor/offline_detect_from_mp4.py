import sys
import os
import shutil
import time
import datetime
import traceback
import threading
import queue
import uuid
import socket
import json
import parse_config
import store_lib
import process_one_video as pov

cfg = parse_config.parse()

queue_obj = queue.Queue()



def check_ffmpeg():
    text = os.popen("ffmpeg --help 2>&1").read()
    #print("ffmpeg output text: ", text)
    if ' version ' in text and ' Copyright ' in text:
        return True
    else:
        return False

def test_check_ffmpeg():
    assert True == check_ffmpeg()

    


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
    assert os.path.exists(cfg['PYTHON_BIN'])
    while 1:
        full_path = q.get()
        if full_path == "poison":
            # this is poison, then exit
            print("thread got poison, then exit")
            break
        else:
            if not store_lib.input_path_file_exists(full_path):
                print("file not exists, full_path: ", full_path)
                continue
            if store_lib.input_path_file_exists(full_path + '.lock'):
                print("lock file alreay exists, then return. full_path: ", full_path)
                continue
            if store_lib.input_path_file_exists(full_path + '.analyze'):
                print("analyze file already exists, then return, full_path: ", full_path)
                continue
            lock_flag = try_lock_file(full_path)
            if lock_flag == False:
                print("lock file failed, then return, full_path: ", full_path)
                continue
            #pov.process_one_video(full_path)
            cmd = r'''{0} offline_detect_from_mp4.py --video_file="{1}" 2>&1 '''.format(cfg['PYTHON_BIN'], full_path)
            print("run cmd: ", cmd)
            #text = os.popen(cmd).read()
            #print("process ret: ", text)
            # write analyze file, and remove lock file
            try:
                print("try to remove lock file")
                if store_lib.input_path_file_exists(full_path + '.lock'):
                    store_lib.delete_input_path_file(full_path + '.lock')
            except:
                traceback.print_exc()


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
                print("b1: ", b1)
                text = b1.decode("utf-8")
                print("lock content: ", text)
                d = json.loads(text)
                if 'createTime' in d:
                    lock_t = datetime.datetime.strptime(d['createTime'], "%Y-%m-%d %H:%M:%S")
                    n = datetime.datetime.now()
                    delta = n - lock_t
                    if delta.seconds > 3600:
                        store_lib.delete_input_path_file(lock)
            except:
                print("delete old lock file Excepttion:")
                traceback.print_exc()

# test case
def test_del_old_lock():
    lock_content1 = '{"createTime": "2022-05-17 00:00:00"}'
    with open("test1.mp4.lock", 'w') as f1:
        f1.write(lock_content1)
    lock_content2 = '{"createTime": "' + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + '"}'
    with open("test2.mp4.lock", 'w') as f2:
        f2.write(lock_content2)
    del_old_lock_files(["test1.mp4.lock", "test2.mp4.lock"])
    assert not os.path.exists("test1.mp4.lock")
    assert os.path.exists("test2.mp4.lock")
    os.remove("test2.mp4.lock")


def filter_by_done_file(video_list, orig_list):
    temp_list_1 = []
    for x in video_list:
        analyze_file = x + '.analyze'
        #print("check analyze file is exists: " + analyze_file)
        if analyze_file not in orig_list:
            temp_list_1.append(x)
    if len(temp_list_1) == 0:
        print("video list is empty after analyze filter, then return")
        return []
    temp_list_2 = []
    for x in temp_list_1:
        done_file = x + '.done'
        #print("check done file is exists: " + done_file)
        if done_file in orig_list:
            temp_list_2.append(x)
    if len(temp_list_2) == 0:
        print("video list is empty after done filter, then return")
        return []
    return temp_list_2

def batch_process():
    #run batch
    print("start one batch process")
    orig_list = store_lib.list_input_path(cfg['input_file_base_path'])
    lock_list = [os.path.join(cfg['input_file_base_path'], x) for x in orig_list if x.endswith(".lock")]
    print("lock_list: ", lock_list)
    del_old_lock_files(lock_list)
    video_list = [x for x in orig_list if x.endswith(".mp4") and '120x' not in x]
    if len(video_list) == 0:
        print("video list is empty, then return")
        return
    video_list.sort()
    video_list = filter_by_done_file(video_list, orig_list)

    if len(video_list) == 0:
        return

    # one batch process 10 files
    if len(video_list) > 30:
        video_list = video_list[:30]
    print("found video list: ", video_list)
    # first start processor threads
    threads = []
    for i in range(cfg['EXECUTOR_NUM']):
        t = threading.Thread(target=process_from_queue, args=(queue_obj,))
        t.setDaemon(True)
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
    print("all thread exited")
                                    

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
            traceback.print_exc()
            return False
        if not store_lib.input_path_file_exists(lockfile):
            # write failed, maybe file path can not be written, return False
            return False
        else:
            str_read = ""
            try:
                temp_bytes = store_lib.read_file_from_input_path(lockfile)
                str_read = temp_bytes.decode("utf-8")
                str_read = str_read.strip("\r\n").strip()
            except:
                traceback.print_exc()
                return False
            if cfg['LOCK_STR'] not in str_read:
                # may be written again be other process or other machine
                return False
            else:
                # !!!!!! SUCCESS lock this file
                return True

def test_lock():
    # test 1
    if os.path.exists("1.txt.lock"):
        os.remove('1.txt.lock')
    full_path = "1.txt"
    assert True == try_lock_file("1.txt")
    if os.path.exists("1.txt.lock"):
        os.remove("1.txt.lock")
    # test 2
    if os.path.exists("2.txt.lock"):
        os.remove('2.txt.lock')
    f2 = open("2.txt.lock", 'w')
    f2.write("1123123")
    f2.close()
    assert False == try_lock_file("2.txt")
    if os.path.exists("2.txt.lock"):
        os.remove("2.txt.lock")


def should_process_now(tstr):
    print("current time: ", tstr)
    if tstr >= '0000' and tstr < cfg['PROCESS_START_TIME']:
        print("should process, return False")
        return False
    if tstr >= cfg['PROCESS_END_TIME'] and tstr <= '2359':
        print("should process, return False")
        return False
    print("should process, return True")
    return True

def test_should_process():
    assert False == should_process_now('0000')
    assert False == should_process_now('0001')
    assert False == should_process_now('0500')
    assert False == should_process_now('0600')
    assert True == should_process_now('0800')
    assert True == should_process_now('1200')
    assert True == should_process_now('1200')
    assert True == should_process_now('1800')
    assert True == should_process_now('1900')
    assert True == should_process_now('2100')
    assert True == should_process_now('2159')
    assert False == should_process_now('2200')
    assert False == should_process_now('2300')
    assert False == should_process_now('2359')

if __name__ == "__main__":
    assert True == check_ffmpeg()
    if '--debug' in sys.argv:
        cfg['DEBUG'] = 1
    for arg in sys.argv:
        if '--video-file=' in arg:
            arg = arg.replace("--video-file=", "--video_file=")
        if '--video_file=' in arg:
            print("process single video file")
            full_path = arg.split("--video_file=")[1]
            if full_path.startswith('"'):
                full_path = full_path.strip('"')
            store_lib.input_path_file_exists(full_path)
            print("full_path: ", full_path)
            pov.process_one_video(full_path)
            sys.exit(0)
        if '--run_it' in arg:
            cfg['DEBUG'] = 1
            run_it()
            sys.exit(0)
    while 1:
        n = datetime.datetime.now()
        tstr = n.strftime("%H%M")
        if should_process_now(tstr):
            try:
                batch_process()
            except:
                print("Error when batch_process")
                traceback.print_exc()
            print("after process, sleep 60")
            time.sleep(60)
        else:
            print("not now, then sleep 60")
            time.sleep(60)

