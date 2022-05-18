import cv2
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

EXECUTOR_NUM = 4

DEBUG = 0
split_limit = 600
area_threh = 9
thres1 = 20
prefix_video_sec = 1.0 # when cut video, keep 1 seconds before meteor
base_output_path = r'W:\meteor_monitor\meteor_store'
input_file_base_path = r'W:\meteor_monitor\origin'
queue_obj = queue.Queue()
LOCK_STR = str(uuid.uuid4())
PROCESS_START_TIME = '0700'
PROCESS_END_TIME = '2200'
IP_ADDR = ""

def get_local_ip():
    ip = ""
    try:
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)
    except:
        pass
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip

def decode_fourcc(cc):
    return "".join([chr((int(cc) >> 8 * i) & 0xFF) for i in range(4)])

def parse_config():
    global EXECUTOR_NUM, PROCESS_START_TIME, PROCESS_END_TIME
    text = ""
    if os.path.exists(".config"):
        f1 = open(".config")
        text = f1.read()
        f1.close()
    for line in text.split("\n"):
        if line.startswith("#"):
            continue
        if 'EXECUTOR_NUM' in line:
            EXECUTOR_NUM = int(line.split("=")[1].strip())
            print("resolve PARAM, EXECUTOR_NUM: ", EXECUTOR_NUM)
        if 'PROCESS_START_TIME' in line:
            PROCESS_START_TIME = line.split("=")[1].strip('"')
            print("resolve PARAM, PROCESS_START_TIME: ", PROCESS_START_TIME)
        if 'PROCESS_END_TIME' in line:
            PROCESS_END_TIME = line.split("=")[1].strip('"')
            print("resolve PARAM, PROCESS_END_TIME: ", PROCESS_END_TIME)


def mask_img(img, w, h):
    mask_file = 'mask-1280-720.bmp'
    if not os.path.exists(mask_file):
        return img
    img_mask = cv2.imread(mask_file)
    if w != 1280:
        img_mask = cv2.resize(img_mask, (w,h))
    ret_img = cv2.bitwise_and(img, img_mask)
    return ret_img

def convert_img(frame):
    resized = cv2.resize(frame,(512,512))
    gray_lwpCV = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    #cv2.imshow('Frame',gray_lwpCV)
    gray_lwpCV = cv2.GaussianBlur(gray_lwpCV, (5, 5), 0)
    #cv2.imshow('Frame',gray_lwpCV)
    return gray_lwpCV, resized

def read_one_frame(vid_capture):
    if not vid_capture.isOpened():
        return False, None
    else:
        ret, frame = vid_capture.read()
        return ret, frame

def check_ffmpeg():
    text = os.popen("ffmpeg --help 2>&1").read()
    #print("ffmpeg output text: ", text)
    if ' version ' in text and ' Copyright ' in text:
        return True
    else:
        return False

def test_check_ffmpeg():
    assert True == check_ffmpeg()

def process_one_frame(data_obj):

    width = data_obj["width"]
    height = data_obj["height"]
    frame_count = data_obj["frame_count"]
    last_cnt = data_obj["last_cnt"]
    background = data_obj["background"]
    cnt = data_obj['frame_idx']
    ret = data_obj["ret"]
    frame = data_obj["frame"]
    # got Finish signal, then break
    if ret == False:
        return
    if cnt == 0:
        cv2.imwrite("1.jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY),100])
    if cnt %200 == 0:
        if cnt > 100:
            t2 = time.time()
            print("process speed, {0} frames per sec".format(int((cnt - last_cnt)/(t2-data_obj['t1']))))
            data_obj["last_cnt"] = cnt
            data_obj['t1'] = t2
        print("frame count: ", cnt, '  total: ', frame_count)
    match = 0
    m_img = mask_img(frame, width, height)
    #cv2.imshow("masked_image", m_img)
    # get background image, every 600 frames
    gray_lwpCV, resized_frame = convert_img(m_img)
    if cnt % split_limit == 0:
        print("set background")
        data_obj['background']=gray_lwpCV
    else:
        diff = cv2.absdiff(background, gray_lwpCV)
        #cv2.imshow("background", background)
        #cv2.imshow("gray_lwpCV", gray_lwpCV)
        #cv2.imshow("diff", diff)
        diff = cv2.threshold(diff, thres1, 255, cv2.THRESH_BINARY)[1]
        ret,thresh = cv2.threshold(diff.copy(),150,255,0)
        #print("thresh: ", thresh)
        contours, hierarchy = cv2.findContours(thresh,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
        #contours, hierarchy = cv2.findContours(diff.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for c in contours:
            if cv2.contourArea(c) < area_threh :
                continue
            else:
                (x, y, w, h) = cv2.boundingRect(c)
                cv2.rectangle(resized_frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                #cv2.imshow("rectangle", frame)
                #print("find diff, frame index: ", cnt, ' rectangle: ', (x,y,w,h))
                match = 1
                data_obj['index'].append(cnt)
    if DEBUG:
        cv2.imshow("frame: ", resized_frame)
    if DEBUG:
        key = cv2.waitKey(50)

    data_obj["frame_idx"] += 1

def read_one_video(full_path):

    vid_capture = cv2.VideoCapture(full_path)
    if (vid_capture.isOpened() == False):
        print("Error opening the video file")
        vid_capture.release()
        return
    width = int(vid_capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    print('video width: ', width)
    height = int(vid_capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print('video height: ', height)
    fourcc = int(vid_capture.get(cv2.CAP_PROP_FOURCC))
    print("fourcc: ", decode_fourcc(fourcc))
    fps = vid_capture.get(cv2.CAP_PROP_FPS)
    print('Frames per second : ', fps,'FPS')
    frame_count = vid_capture.get(7)
    print('Frame count : ', frame_count)
    time_sec = frame_count / fps
    print("time total seconds: ", time_sec)
    index = []
    data_obj = {
        "frame_idx": 0,
        "index": index,
        "width": width,
        "height": height,
        "frame_count": frame_count,
        "background": None,
        "last_cnt": 0,
        "t1": time.time(),
    }
    while 1:
        ret, frame = read_one_frame(vid_capture)
        data_obj["ret"] = ret
        data_obj['frame'] = frame
        if ret == False:
            break
        process_one_frame(data_obj)

    vid_capture.release()
    print("index: ", index)
    return index, frame_count, fps, time_sec

def seconds_to_hum_readable(secs):
    h = secs / 3600
    secs = secs % 3600
    m = secs / 60
    secs = secs % 60
    s = secs
    #return '%d:%d:%d'%(h, m, s)
    return '%02d:%02d:%02d'%(h, m, s)

def test_seconds_to_hum_readable():
    assert '00:01:31' == seconds_to_hum_readable(91)
    assert '00:11:01' == seconds_to_hum_readable(661)
    assert '00:11:59' == seconds_to_hum_readable(719)
    assert '01:00:01' == seconds_to_hum_readable(3601)


def gen_ffmpg_split_cmd(start_time, end_time, input_file, base_path):
    t = get_record_time_from_video_name(input_file, start_time)
    date = t.strftime("%Y%m%d")
    out_dir = os.path.join(base_path, date)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    out_file = t.strftime("%Y%m%d_%H%M%S.mp4")
    out_full_path = os.path.join(out_dir, out_file)
    if os.path.exists(out_full_path):
        os.remove(out_full_path)
    cmd = 'ffmpeg -ss "{0}" -t "{1}" -i "{2}" -vcodec copy -acodec copy "{3}" 2>&1 '.format(
            start_time, end_time, input_file, out_full_path)
    return cmd

def get_record_time_from_video_name(full_path, shift_time):
    basename = os.path.basename(full_path)
    t = datetime.datetime.strptime(basename, "WIN_%Y%m%d_%H_%M_%S_Pro.mp4")
    shift_hour = shift_time.split(":")[0]
    shift_min = shift_time.split(":")[1]
    shift_sec = shift_time.split(":")[2]
    seconds = int(shift_hour) * 3600 + int(shift_min) * 60 + int(shift_sec)
    t2 = t + datetime.timedelta(seconds = seconds)
    return t2
    

def test_get_record_time():
    p = r'W:\meteor_monitor\origin\WIN_20220514_04_54_56_Pro.mp4'
    t = get_record_time_from_video_name(p, '00:00:01')
    assert '2022-05-14 04:54:57' == t.strftime("%Y-%m-%d %H:%M:%S")
    p = r'W:\meteor_monitor\origin\WIN_20220514_04_54_56_Pro.mp4'
    t = get_record_time_from_video_name(p, '00:09:01')
    assert '2022-05-14 05:03:57' == t.strftime("%Y-%m-%d %H:%M:%S")
    p = r'W:\meteor_monitor\origin\WIN_20220514_04_54_56_Pro.mp4'
    t = get_record_time_from_video_name(p, '01:09:01')
    assert '2022-05-14 06:03:57' == t.strftime("%Y-%m-%d %H:%M:%S")

def test_get_segments():
    index = []
    segments = get_segments_from_index(index)
    assert segments == []

    index = [31]
    segments = get_segments_from_index(index)
    assert segments == [[31, 31]]

    index = [31,32,33]
    segments = get_segments_from_index(index)
    assert segments == [[31, 33]]

    index = [31, 32, 35]
    segments = get_segments_from_index(index)
    assert segments == [[31, 32], [35, 35]]

    index = [31,32,33,34,35,145,146,147,148,150]
    segments = get_segments_from_index(index)
    assert segments == [[31, 35], [145, 148], [150, 150]]

def get_segments_from_index(index):
    #print("get_segments_from_index entry, index: ", index)
    segments = []
    begin = None
    mid = None
    end = None
    for i in index:
        if begin == None:
            begin = i
            mid = i
            end = i
        else:
            if i == mid + 1:
                mid = i
                end = i
            else:
                # end one segment
                segments.append([begin, end])
                begin = i
                mid = i
                end = i
    if begin != None:
        segments.append([begin, end])
    #print("get segment return , segments: ", segments)
    return segments

def test_merge_segments():
    segments = []
    assert [] == merge_segments(segments, 25)
    segments = [[31, 35], [80, 81]]
    assert [[31, 81]] == merge_segments(segments, 25)
    segments = [[1000, 1080], [1300, 1301], [1303, 1320]]
    assert [[1000, 1080], [1300, 1320]] == merge_segments(segments, 25)
    segments = [[1000, 1080], [1090, 1092], [1190, 1192], [1290, 1292], [1390, 1391]]
    assert [[1000, 1391]] == merge_segments(segments, 25)
    segments = [[1000, 1080], [1090, 1092], [1190, 1192], [1290, 1292], [1390, 1391], [2200, 2275]]
    assert [[1000, 1391], [2200, 2275]] == merge_segments(segments, 25)
    segments = [[500, 500],[1500,1500],[2500, 2500]]
    assert  [[500, 500],[1500,1500],[2500,2500]] == merge_segments(segments, 50)

def merge_segments(segments, fps):
    last_begin = -1
    last_end = -1
    out_segments = []
    if len(segments) == 0:
        return out_segments
    # if distance between 2 segments is too near, then merge them
    for i in range(len(segments)):
        seg = segments[i]
        begin, end = seg
        if last_end == -1:
            last_begin = begin
            last_end = end 
        # calc distance
        else:
            if begin - last_end < 5 * fps:
                last_end = end
            else:
                out_segments.append([last_begin, last_end])
                last_begin = begin
                last_end = end
    if segments[-1][1] == last_end:
        out_segments.append([last_begin, last_end])
    return out_segments

def test_calc_begin_time_and_duration():
    segments = [1, 80]
    begin_time, duration = calc_begin_time_and_duration(segments, 25)
    assert begin_time == 0 and duration == 7

    segments = [25, 80]
    begin_time, duration = calc_begin_time_and_duration(segments, 25)
    assert begin_time == 0 and duration == 6

    segments = [78, 80]
    begin_time, duration = calc_begin_time_and_duration(segments, 25)
    assert begin_time == 1 and duration == 4

    segments = [601, 690]
    begin_time, duration = calc_begin_time_and_duration(segments, 48)
    assert begin_time == 10 and duration == 5


def calc_begin_time_and_duration(segment, fps):
    begin, end = segment
    frame_len = end - begin
    duration = int((float(frame_len) / fps)) #
    duration += 4
    begin_time = int(float(begin) / fps)
    begin_time -= 2
    if begin_time < 0:
        begin_time = 0
    return begin_time, duration

def calc_split_range(index, frame_count, fps, time_sec):
    l = prefix_video_sec
    # first find multiple segment
    segments = get_segments_from_index(index)
    # then merge near segments
    new_segments = merge_segments(segments, fps)
    param_list = []
    for seg in new_segments:
        begin_time, duration = calc_begin_time_and_duration(seg, fps)
        begin_time_hum = seconds_to_hum_readable(begin_time)
        duration_hum = seconds_to_hum_readable(duration)
        param_list.append([begin_time_hum, duration_hum])
    return param_list
        
def process_one_video(full_path):
    print("processing video, ", full_path)
    ret = read_one_video(full_path)
    index, frame_count, fps, time_sec = ret
    param_list = calc_split_range(index, frame_count, fps, time_sec)
    if len(param_list) > 0:
        for param in param_list:
            cmd = gen_ffmpg_split_cmd(param[0], param[1], full_path, base_output_path)
            print("run ffmpeg, cmd: ", cmd)
            if DEBUG == 0:
                text = os.popen(cmd).read()
                print("cmd ret: ", text)

    print("try to create .analyze file")
    with open(full_path + '.analyze', 'w') as f2:
        f2.write("IP:" + IP_ADDR + "\n" + "index: " + str(index))
def run_it():
    #read_one_video("1.mp4")
    #process_one_video(os.path.join("test-T", "WIN_20220507_03_23_22_Pro.mp4"))
    #process_one_video(os.path.join("test-F", "WIN_20220518_03_26_44_Pro.mp4"))
    #process_one_video(os.path.join("test-F", "WIN_20220518_04_10_47_Pro.mp4"))
    process_one_video(os.path.join("test-F", "WIN_20220518_02_35_56_Pro.mp4"))
    #read_one_video("meteor-20211228.mp4")
    #read_one_video("meteor-20211229.mp4")
    #read_one_video("meteor-20211231.mp4")


def process_from_queue(q):
    while 1:
        full_path = q.get()
        if full_path == "poison":
            # this is poison, then exit
            print("thread got poison, then exit")
            break
        else:
            if not os.path.exists(full_path):
                print("file not exists, full_path: ", full_path)
                continue
            if os.path.exists(full_path + '.lock'):
                print("lock file alreay exists, then return. full_path: ", full_path)
                continue
            if os.path.exists(full_path + '.analyze'):
                print("analyze file already exists, then return, full_path: ", full_path)
                continue
            lock_flag = try_lock_file(full_path)
            if lock_flag == False:
                print("lock file failed, then return, full_path: ", full_path)
                continue
            #process_one_video(full_path)
            cmd = r'''python offline_detect_from_mp4.py --video_file="{0}" 2>&1 '''.format(full_path)
            print("run cmd: ", cmd)
            text = os.popen(cmd).read()
            print("process ret: ", text)
            # write analyze file, and remove lock file
            try:
                print("try to remove lock file")
                if os.path.exists(full_path + '.lock'):
                    os.remove(full_path + '.lock')
            except:
                traceback.print_exc()


def batch_process():
    #run batch
    print("start one batch process")
    video_list = os.listdir(input_file_base_path)
    video_list = [x for x in video_list if x.endswith(".mp4")]
    if len(video_list) == 0:
        print("video list is empty, then return")
        return
    video_list.sort()
    video_list = [x for x in video_list if not os.path.exists(os.path.join(input_file_base_path, x + '.analyze'))]
    if len(video_list) == 0:
        print("video list is empty after analyze filter, then return")
        return
    video_list = [x for x in video_list if os.path.exists(os.path.join(input_file_base_path, x + '.done'))]
    if len(video_list) == 0:
        print("video list is empty after done filter, then return")
        return
    # one batch process 10 files
    if len(video_list) > 30:
        video_list = video_list[:30]
    print("found video list: ", video_list)
    # first start processor threads
    threads = []
    for i in range(EXECUTOR_NUM):
        t = threading.Thread(target=process_from_queue, args=(queue_obj,))
        t.setDaemon(True)
        t.start()
        threads.append(t)
    # get video list,  put them to queue
    for video_file in video_list:
        full_path = os.path.join(input_file_base_path, video_file)
        done_file = os.path.join(input_file_base_path, video_file + '.done')
        queue_obj.put(full_path)
    # generate poison for each thread
    for i in range(EXECUTOR_NUM):
        queue_obj.put("poison")
    # wait thread to exit
    for t in threads:
        t.join()
    print("all thread exited")
                                    

def try_lock_file(full_path):
    lockfile = full_path + ".lock"
    if os.path.exists(lockfile):
        return False
    else:
        try:
            with open(lockfile, 'w') as f1:
                f1.write(LOCK_STR + "\t" + "IP:" + IP_ADDR)
        except:
            return False
        if not os.path.exists(lockfile):
            # write failed, maybe file path can not be written, return False
            return False
        else:
            str_read = ""
            try:
                with open(lockfile, 'r') as f2:
                    str_read = f2.read().strip("\r\n").strip()
            except:
                return False
            if LOCK_STR not in str_read:
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
    if tstr >= '0000' and tstr < PROCESS_START_TIME:
        print("should process, return False")
        return False
    if tstr >= PROCESS_END_TIME and tstr <= '2359':
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
    IP_ADDR = get_local_ip()
    print("IP: ", IP_ADDR)
    parse_config()
    for arg in sys.argv:
        if '--video_file=' in arg:
            print("process single video file")
            full_path = arg.split("--video_file=")[1]
            if full_path.startswith('"'):
                full_path = full_path.strip('"')
            assert os.path.exists(full_path)
            print("full_path: ", full_path)
            process_one_video(full_path)
            sys.exit(0)
        if '--run_it' in arg:
            DEBUG = 1
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

