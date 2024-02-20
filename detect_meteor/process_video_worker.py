import queue
import threading
import os
from logzero import logger
import store_lib

queue_obj = queue.Queue()
cfg = parse_config.parse()

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
                                    

def process_from_queue(q):
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
            cmd = r'''{0} process_one_video.py "{1}"  2>&1 '''.format(cfg['PYTHON_BIN'], full_path)
            logger.info("run cmd: " + cmd)
            text = os.popen(cmd).read()
            logger.info("process ret: " + text)
            # write analyze file, and remove lock file
            try:
                logger.info("try to remove lock file")
                if store_lib.input_path_file_exists(full_path + '.lock'):
                    store_lib.delete_input_path_file(full_path + '.lock')
            except:
                logger.warning(traceback.format_exc())




def loop_process_video():
    while 1:
        time.sleep(10)
        flag1 = util.should_process_now()
        flag2 = int(cfg['ALWAYS_PROCESS']) == 1
        logger.info("flag1: %d, flag2: %d", flag1, flag2)
        if flag1 or flag2:
            if flag1:
                logger.info("sould process get True, process begin")
            if flag2:
                logger.info("always process config get 1, process begin")
            try:
                batch_process()
            except:
                logger.warning("Error when batch_process")
                logger.warning(traceback.format_exc())
            logger.info("after process, sleep 30")
            time.sleep(30)





