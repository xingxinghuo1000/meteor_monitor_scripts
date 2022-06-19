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
import json
import numpy as np

EXECUTOR_NUM = 4

DEBUG = 0
split_limit = 100
area_threh = 5
thres1 = 20
prefix_video_sec = 1.0 # when cut video, keep 1 seconds before meteor
base_output_path = r'W:\meteor_monitor\meteor_store'
input_file_base_path = r'W:\meteor_monitor\origin'
queue_obj = queue.Queue()
LOCK_STR = str(uuid.uuid4())
PROCESS_START_TIME = '0700'
PROCESS_END_TIME = '2200'
IP_ADDR = ""
PYTHON_BIN = "python"
temp_time_elapse_video_dir = os.path.join(os.getcwd(), "temp")

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
    global EXECUTOR_NUM, PROCESS_START_TIME, PROCESS_END_TIME, base_output_path, input_file_base_path, PYTHON_BIN
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
            PROCESS_START_TIME = line.split("=")[1].strip(' "')
            print("resolve PARAM, PROCESS_START_TIME: ", PROCESS_START_TIME)
        if 'PROCESS_END_TIME' in line:
            PROCESS_END_TIME = line.split("=")[1].strip(' "')
            print("resolve PARAM, PROCESS_END_TIME: ", PROCESS_END_TIME)
        if 'base_output_path' in line:
            base_output_path = line.split("=")[1].strip(' "')
            print("resolve PARAM, base_output_path: ", base_output_path)
        if 'input_file_base_path' in line:
            input_file_base_path = line.split("=")[1].strip(' "')
            print("resolve PARAM, input_file_base_path: ", input_file_base_path)
        if 'PYTHON_BIN' in line:
            PYTHON_BIN = line.split("=")[1].strip(' "')
            print("resolve PARAM, PYTHON_BIN: ", PYTHON_BIN)

img_mask = None
has_load_img_mask = 0
def mask_img(full_path, img, w, h):
    global img_mask, has_load_img_mask
    if has_load_img_mask == 0:
        base_dir = os.path.dirname(full_path)
        mask_file1 = os.path.join(base_dir, 'mask-1280-720.bmp')
        mask_file2 = 'mask-1280-720.bmp'
        
        if not os.path.exists(mask_file1) and not os.path.exists(mask_file1):
            return img
        if os.path.exists(mask_file1):
            img_mask = cv2.imread(mask_file1)
        else: 
            if os.path.exists(mask_file2):
                img_mask = cv2.imread(mask_file2)
        if w != 1280:
            img_mask = cv2.resize(img_mask, (w,h))
        has_load_img_mask = 1
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


last_5_frame = []
def save_recent_frames(img, frame_list):
    if len(frame_list) > 10:
        del frame_list[0]
    frame_list.append(img)

def get_recent_avg_img(frames):
    #return frames[-1]
    #cv2.imshow("one", frames[0])
    median = np.median(frames, axis=0).astype(dtype=np.uint8)
    #cv2.imshow("median", median)
    return median

es = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 4))
# quote from : https://blog.csdn.net/drippingstone/article/details/116081434， 帧差法基本原理和实现
# quote from : https://www.cnblogs.com/my-love-is-python/p/10394908.html 形态学腐蚀和膨胀
def process_one_frame(data_obj):

    width = data_obj["width"]
    height = data_obj["height"]
    frame_count = data_obj["frame_count"]
    last_cnt = data_obj["last_cnt"]
    background = data_obj["background"]
    cnt = data_obj['frame_idx']
    ret = data_obj["ret"]
    frame = data_obj["frame"]
    filter_info_list = data_obj["filter_info_list"]
    full_path = data_obj['full_path']
    # got Finish signal, then break
    if ret == False:
        return
    if cnt %200 == 0:
        if cnt > 100:
            t2 = time.time()
            print("process speed, {0} frames per sec".format(int((cnt - last_cnt)/(t2-data_obj['t1']))))
            data_obj["last_cnt"] = cnt
            data_obj['t1'] = t2
        print("frame count: ", cnt, '  total: ', frame_count)
    match = 0
    
    m_img = mask_img(full_path, frame, width, height)
    #cv2.imshow("masked_image", m_img)
    # get background image, every 600 frames
    # 对帧进行预处理，先转灰度图，再进行高斯滤波。
    # 用高斯滤波进行模糊处理，进行处理的原因：每个输入的视频都会因自然震动、光照变化或者摄像头本身等原因而产生噪声。对噪声进行平滑是为了避免在运动和跟踪时将其检测出来。
    gray_lwpCV, resized_frame = convert_img(m_img)
    # save recent 5 frames, for further purpose
    save_recent_frames(gray_lwpCV, last_5_frame)
    if cnt % split_limit == 0:
        print("set background")
        data_obj['background'] = get_recent_avg_img(last_5_frame)
        cv2.imwrite("back.jpg", data_obj['background'], [int(cv2.IMWRITE_JPEG_QUALITY),100])
        cv2.imwrite("one.jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY),100])
    else:
        # 对于每个从背景之后读取的帧都会计算其与北京之间的差异，并得到一个差分图（different map）
        diff = cv2.absdiff(background, gray_lwpCV)
        #cv2.imshow("background", background)
        #cv2.imshow("gray_lwpCV", gray_lwpCV)
        #cv2.imshow("diff", diff)
        # 还需要应用阈值来得到一幅黑白图像，并通过下面代码来膨胀（dilate）图像，从而对孔（hole）和缺陷（imperfection）进行归一化处理
        diff2 = cv2.threshold(diff, thres1, 255, cv2.THRESH_BINARY)[1] # 二值化处理
        diff3 = cv2.threshold(diff2,150,255,0)[1]
        #diff4 = cv2.dilate(diff3, es, iterations=2) # 形态学膨胀
        contours, hierarchy = cv2.findContours(diff3, cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
        for c in contours:
            area = cv2.contourArea(c)
            if area < area_threh :
                #filter_info_list.append(item)
                continue
            if area > int(512*512*0.5):
                print("area: ", area)
                print("SKIP this frame, filter by area too big")
                item = {
                    "filter_reason": "area too big", 
                    "c": "w, y, w, h: " + str(cv2.boundingRect(c)), 
                    "frame_idx": cnt
                }
                filter_info_list.append(item)
                continue
            (x, y, w, h) = cv2.boundingRect(c)
            #x -= 2
            #y -= 2
            #w += 2
            #h += 2
            crop_diff = gray_lwpCV[y:y+h, x:x+w]
            crop_orig = background[y:y+h, x:x+w]
            mean_crop_diff = cv2.mean(crop_diff)[0]
            mean_crop_orig = cv2.mean(crop_orig)[0]
            # condition 1, lightness < orgin
            if mean_crop_diff < mean_crop_orig:
                print("mean_crop_diff: ", mean_crop_diff)
                print("mean_crop_orig: ", mean_crop_orig)
                print("SKIP this frame, filter by bird bug or bat")
                item = {
                    "filter_reason": " bird bug or bat", 
                    "c": "w, y, w, h: " + str((x,y,w,h)), 
                    "frame_idx": cnt
                }
                filter_info_list.append(item)
                continue
            cv2.rectangle(resized_frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            print("find diff, frame index: ", cnt, ' rectangle: ', (x,y,w,h))

            match = 1
        if match == 1:
            if DEBUG:
                key = cv2.waitKey(200)
            data_obj['index'].append(cnt)
    if DEBUG:
        cv2.imshow("frame: ", resized_frame)
    if DEBUG:
        key = cv2.waitKey(5)

    data_obj["frame_idx"] += 1

def read_one_video(full_path):

    vid_capture = cv2.VideoCapture(full_path)
    if (vid_capture.isOpened() == False):
        print("Error opening the video file")
        vid_capture.release()
        return [], -1, -1, -1
    width = int(vid_capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    print('video width: ', width)
    height = int(vid_capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print('video height: ', height)
    fourcc = int(vid_capture.get(cv2.CAP_PROP_FOURCC))
    print("fourcc: ", decode_fourcc(fourcc))
    fps = vid_capture.get(cv2.CAP_PROP_FPS)
    print('Frames per second : ', int(fps),'FPS')
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
        "fps": fps,
        "time_sec": time_sec,
        "background": None,
        "last_cnt": 0,
        "t1": time.time(),
        "filter_info_list": [],
        "full_path": full_path,
    }
    while 1:
        ret, frame = read_one_frame(vid_capture)
        data_obj["ret"] = ret
        data_obj['frame'] = frame
        if ret == False:
            break
        process_one_frame(data_obj)
        process_time_elapse_one_frame(data_obj)

    vid_capture.release()
    if 'elapse_120x' in data_obj:
        data_obj['elapse_120x'].release()
        convert_avi_to_264(data_obj['elapse_120x_fn'])
    print("index: ", index)
    print("filter_info_list: ", data_obj['filter_info_list'])
    return data_obj

def convert_avi_to_264(full_name):
    print("convert avi to h264")
    name = os.path.basename(full_name)
    h264_name = name.replace(".avi", "") + ".mp4"
    h264_name = os.path.join(input_file_base_path, h264_name)
    if os.path.exists(h264_name):
        os.remove(h264_name)
    cmd = r'''ffmpeg -i "{0}"  -c:v h264 -b:v 8000k -strict -2  "{1}" 2>&1'''.format(
        full_name, h264_name)
    print("cmd: ", cmd)
    ret = os.popen(cmd).read()
    print("ffmpeg output:\n" + ret)
    os.remove(full_name)
    assert os.path.exists(h264_name)

frames_elapse = []
def process_time_elapse_one_frame(data_obj):
    global frames_elapse
    if 'elapse_120x' not in data_obj:
        base_dir = os.path.dirname(data_obj['full_path'])
        name = os.path.basename(data_obj['full_path']).replace(".mp4", "")
        name += '.120x.avi'
        if not os.path.exists(temp_time_elapse_video_dir):
            os.makedirs(temp_time_elapse_video_dir)
        fn = os.path.join(temp_time_elapse_video_dir, name)
        data_obj['elapse_120x_fn'] = fn
        if os.path.exists(fn):
            os.remove(fn)
        videoWriter = cv2.VideoWriter(fn, 
            cv2.VideoWriter_fourcc('I', '4', '2', '0'), 
            data_obj['fps'], 
            (data_obj['width'],data_obj['height']))
        data_obj['elapse_120x'] = videoWriter
    if data_obj['frame_idx'] % 120 < 3:
        frames_elapse.append(data_obj['frame'])
    if data_obj['frame_idx'] % 120 == 3:
        m = get_recent_avg_img(frames_elapse)
        frames_elapse = []
        data_obj['elapse_120x'].write(m)

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
    p = os.path.join(input_file_base_path, 'WIN_20220514_04_54_56_Pro.mp4')
    t = get_record_time_from_video_name(p, '00:00:01')
    assert '2022-05-14 04:54:57' == t.strftime("%Y-%m-%d %H:%M:%S")
    p = os.path.join(input_file_base_path, 'WIN_20220514_04_54_56_Pro.mp4')
    t = get_record_time_from_video_name(p, '00:09:01')
    assert '2022-05-14 05:03:57' == t.strftime("%Y-%m-%d %H:%M:%S")
    p = os.path.join(input_file_base_path, 'WIN_20220514_04_54_56_Pro.mp4')
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
    t1 = time.time()
    ret = read_one_video(full_path)
    t2 = time.time()
    index = ret['index']
    frame_count = ret['frame_count']
    fps = ret['fps']
    time_sec = ret['time_sec']
    filter_info_list = ret['filter_info_list']
    if len(index) > 0 and DEBUG == 0:
        process_speed = int(frame_count / (t2-t1))
        param_list = calc_split_range(index, frame_count, fps, time_sec)
        if len(param_list) > 0:
            for param in param_list:
                cmd = gen_ffmpg_split_cmd(param[0], param[1], full_path, base_output_path)
                print("run ffmpeg, cmd: ", cmd)
                if DEBUG == 0:
                    text = os.popen(cmd).read()
                    print("cmd ret: ", text)
    print("process time: ", int(t2-t1))
    print("process speed fps: ", int(frame_count/(t2-t1)))
    write_analyze(full_path, IP_ADDR, index, frame_count, t2-t1, time_sec, filter_info_list)

def write_analyze(full_path, ip, index, frame_count, time_use, video_time_sec, filter_info_list):
    ana_file = full_path + '.analyze'
    process_speed = int(frame_count/time_use)
    print("try to create .analyze file, path: ", ana_file)
    d = {}
    d["IP"] = ip
    d["index"] = index
    d["process speed fps"] = process_speed
    d['process time second'] = int(time_use)
    d['video length second'] = int(video_time_sec)
    d['filter_info_list'] = filter_info_list
    text = json.dumps(d, ensure_ascii=False, indent=2)
    if DEBUG:
        print("analyze result:\n" + text)
    else:
        with open(full_path + '.analyze', 'w') as f2:
            f2.write(text)

def test_write_analyze_file():
    full_path = "1.mp4"
    write_analyze(full_path, '1.1.1.1', [], 7000, 700, 150)
    assert os.path.exists("1.mp4.analyze")
    with open("1.mp4.analyze") as f1:
        text = f1.read()
        assert "IP: 1.1.1.1" in text
        assert "index:[]" in text
        assert "process speed: 10 frames per second" in text
        assert "process time: 700 seconds" in text
        assert "video length: 150 seconds" in text
    os.remove("1.mp4.analyze")

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
            cmd = r'''{0} offline_detect_from_mp4.py --video_file="{1}" 2>&1 '''.format(PYTHON_BIN, full_path)
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


# If process is killed, then lock file will be remained as trash
# If the old lock is not deleted, then this video file will never be processed in the future
# So in every loop, 
# we will check lock file is too old, >= 3600 seconds, if True, then delete it
def del_old_lock_files(lock_list):
    # read lock content
    for lock in lock_list:
        if os.path.exists(lock):
            try:
                f1 = open(lock)
                text = f1.read()
                print("lock content: ", text)
                f1.close()
                d = json.loads(text)
                if 'createTime' in d:
                    lock_t = datetime.datetime.strptime(d['createTime'], "%Y-%m-%d %H:%M:%S")
                    n = datetime.datetime.now()
                    delta = n - lock_t
                    if delta.seconds > 3600:
                        os.remove(lock)
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

def batch_process():
    #run batch
    print("start one batch process")
    orig_list = os.listdir(input_file_base_path)
    lock_list = [os.path.join(input_file_base_path, x) for x in orig_list if x.endswith(".lock")]
    del_old_lock_files(lock_list)
    video_list = [x for x in orig_list if x.endswith(".mp4")]
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
            d = {
                "createTime": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                "IP": IP_ADDR,
                "LOCK_STR": LOCK_STR
            }
            lock_content = json.dumps(d)
            with open(lockfile, 'w') as f1:
                f1.write(lock_content)
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
    if '--debug' in sys.argv:
        DEBUG = 1
    for arg in sys.argv:
        if '--video-file=' in arg:
            arg = arg.replace("--video-file=", "--video_file=")
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

