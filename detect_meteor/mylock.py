import json
import os
import datetime

import store_lib

from logzero import logger

cfg = parse_config.parse()

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
                d = {}
                try:
                    d = json.loads(text)
                except:
                    logger.info("not valid json format, then delete this lock")
                    store_lib.delete_input_path_file(lock)
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
                logger.warning("delete old lock file Excepttion:")
                logger.warning(traceback.format_exc())

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
            logger.warning(traceback.format_exc())
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
                logger.warning(traceback.format_exc())
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




