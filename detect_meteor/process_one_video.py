import cv2
import os
import time
import datetime
import json
import traceback
import numpy as np
import util
import imageio

import parse_config
import store_lib
from logzero import logger

cfg = parse_config.parse()

MAX_DIFF_FRAME_CNT = 100
split_limit = 30
area_threh = 5
thres1 = 20
prefix_video_sec = 1.0 # when cut video, keep 1 seconds before meteor



temp_time_elapse_video_dir = os.path.join(os.getcwd(), "temp")


def decode_fourcc(cc):
    return "".join([chr((int(cc) >> 8 * i) & 0xFF) for i in range(4)])




img_mask = None
has_mask = 0
has_load_img_mask = 0
def mask_img(origin_path, img, w, h):
    global img_mask, has_load_img_mask, has_mask
    if has_load_img_mask == 0:
        base_dir = os.path.dirname(origin_path)
        mask_file1 = os.path.join(base_dir, 'mask-1280-720.bmp')
        mask_file2 = 'mask-1280-720.bmp'
        logger.info("try to find mask file1: " + mask_file1) 
        logger.info("try to find mask file2: " + mask_file2) 
        if not store_lib.input_path_file_exists(mask_file1) and not os.path.exists(mask_file2):
            logger.info("can not find mask file")
            has_load_img_mask = 1
            return img
        if store_lib.input_path_file_exists(mask_file1):
            logger.info("find image mask file1, path: " + mask_file1)
            tmp_bmp_file = store_lib.gen_local_temp_file() + ".bmp"
            store_lib.fetch_file_from_input_path(mask_file1, tmp_bmp_file)
            assert os.path.exists(tmp_bmp_file)
            img_mask = cv2.imread(tmp_bmp_file)
            has_mask = 1
            util.safe_os_remove(tmp_bmp_file)
            if w != 1280:
                img_mask = cv2.resize(img_mask, (w,h))
        else: 
            if os.path.exists(mask_file2):
                logger.info("find image mask file2, path: " + mask_file2)
                img_mask = cv2.imread(mask_file2)
                has_mask = 1
                if w != 1280:
                    img_mask = cv2.resize(img_mask, (w,h))
        has_load_img_mask = 1
    if has_mask == 1:
        ret_img = cv2.bitwise_and(img, img_mask)
        return ret_img
    else:
        return img

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
    origin_path = data_obj['origin_path']
    # got Finish signal, then break
    if ret == False:
        return
    if cnt %200 == 0:
        if cnt > 100:
            t2 = time.time()
            logger.info("process speed, {0} frames per sec".format(int((cnt - last_cnt)/(t2-data_obj['t1']))))
            data_obj["last_cnt"] = cnt
            data_obj['t1'] = t2
        logger.info("frame count: {0}  total: {1}".format(cnt, frame_count))
    match = 0
    match_rec = None
    
    m_img = mask_img(origin_path, frame, width, height)
    #cv2.imshow("masked_image", m_img)
    # get background image, every 600 frames
    # 对帧进行预处理，先转灰度图，再进行高斯滤波。
    # 用高斯滤波进行模糊处理，进行处理的原因：每个输入的视频都会因自然震动、光照变化或者摄像头本身等原因而产生噪声。对噪声进行平滑是为了避免在运动和跟踪时将其检测出来。
    gray_lwpCV, resized_frame = convert_img(m_img)

    # save recent 5 frames, for further purpose
    save_recent_frames(gray_lwpCV, last_5_frame)
    if cnt % split_limit == 0:
        logger.info("set background")
        data_obj['background'] = get_recent_avg_img(last_5_frame)

        if cfg['DEBUG']:
            cv2.imwrite("back.jpg", data_obj['background'], [int(cv2.IMWRITE_JPEG_QUALITY),100])

        if cfg['DEBUG']:
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
                logger.info("area: " + str(area))
                logger.info("SKIP this frame, filter by area too big")
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
                logger.info("mean_crop_diff: " + str(mean_crop_diff))
                logger.info("mean_crop_orig: " + str(mean_crop_orig))
                logger.info("SKIP this frame, filter by bird bug or bat")
                item = {
                    "filter_reason": " bird bug or bat", 
                    "c": "w, y, w, h: " + str((x,y,w,h)), 
                    "frame_idx": cnt
                }
                filter_info_list.append(item)
                continue
            cv2.rectangle(resized_frame, (x-5, y-5), (x+w+5, y+h+5), (0, 255, 0), 2)
            logger.info("find diff, frame index: " + str(cnt) + ' rectangle: ' +  str((x,y,w,h)))

            match = 1
            match_rec = (x,y,w,h)
        if match == 1:
            if cfg['DEBUG']:
                key = cv2.waitKey(200)
            data_obj['index'].append(cnt)
            data_obj['index_with_rec'].append({"index": cnt, "rec": match_rec})
            # save diff frame for debug
            if len(data_obj['diff_frames_by_index']) < MAX_DIFF_FRAME_CNT:
                tmp_jpg = store_lib.gen_local_temp_file() + ".jpg"
                cv2.imwrite(tmp_jpg, resized_frame, [int(cv2.IMWRITE_JPEG_QUALITY),100])
                gif_frame = imageio.imread(tmp_jpg)
                data_obj['diff_frames_by_index'][str(cnt)] = gif_frame
                logger.info("save diff frame, current total frame num: {0}, cur idx:{1}".format(
                        len(data_obj['diff_frames_by_index']), 
                        cnt))
                util.safe_os_remove(tmp_jpg)
    if cfg['DEBUG']:
        cv2.imshow("frame: ", resized_frame)
    if cfg['DEBUG']:
        key = cv2.waitKey(5)

    data_obj["frame_idx"] += 1






def read_one_video(local_video_path, origin_path):
    vid_capture = cv2.VideoCapture(local_video_path)
    if (vid_capture.isOpened() == False):
        logger.info("Error opening the video file")
        vid_capture.release()
        return None
    width = int(vid_capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    logger.info('video width: ' + str(width))
    height = int(vid_capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    logger.info('video height: ' + str(height))
    fourcc = int(vid_capture.get(cv2.CAP_PROP_FOURCC))
    logger.info("fourcc: " + str(decode_fourcc(fourcc)))
    fps = vid_capture.get(cv2.CAP_PROP_FPS)
    logger.info('Frames per second : ' + str(int(fps)) + 'FPS')
    frame_count = vid_capture.get(7)
    logger.info('Frame count : ' + str(frame_count))
    time_sec = frame_count / fps
    logger.info("time total seconds: " + str(time_sec))
    index = []
    index_with_rec = []
    diff_frames_by_index = {}
    data_obj = {
        "frame_idx": 0,
        "index": index,
        "index_with_rec": index_with_rec,
        "diff_frames_by_index": diff_frames_by_index,
        "width": width,
        "height": height,
        "frame_count": frame_count,
        "fps": fps,
        "time_sec": time_sec,
        "background": None,
        "last_cnt": 0,
        "t1": time.time(),
        "filter_info_list": [],
        "full_path": local_video_path,
        "origin_path": origin_path,
    }
    while 1:
        ret, frame = read_one_frame(vid_capture)
        data_obj["ret"] = ret
        data_obj['frame'] = frame
        if ret == False:
            break
        process_one_frame(data_obj)
        # if set save time elapse video, then record it
        if int(cfg['RECORD_TIME_ELAPSE_VIDEO']) == 1:
            process_time_elapse_one_frame(data_obj)

    vid_capture.release()
    if 'elapse_60x' in data_obj:
        data_obj['elapse_60x'].release()
        convert_avi_to_264(data_obj['elapse_60x_fn'])
    logger.info("index: " + str(index))
    logger.info("filter_info_list: " + str(data_obj['filter_info_list']))
    return data_obj



def convert_avi_to_264(avi_file):
    logger.info("convert avi to h264")
    name = os.path.basename(avi_file)
    h264_basename = name.replace(".avi", "") + ".mp4"
    local_file = os.path.join("temp", h264_basename)
    if os.path.exists(local_file):
        util.safe_os_remove(local_file)
    cmd = r'''ffmpeg -i "{0}"  -c:v h264 -b:v 8000k -strict -2  "{1}" 2>&1'''.format(
        avi_file, local_file)
    logger.info("cmd: " + cmd)
    ret = os.popen(cmd).read()
    logger.info("ffmpeg output:\n" + ret)
    util.safe_os_remove(avi_file)
    assert os.path.exists(local_file)
    remote_file = os.path.join(cfg['input_file_base_path'], h264_basename)
    store_lib.store_file_to_input_path(local_file, remote_file)
    util.safe_os_remove(local_file)

frames_elapse = []
def process_time_elapse_one_frame(data_obj):
    global frames_elapse
    if 'elapse_60x' not in data_obj:
        name = os.path.basename(data_obj['full_path']).replace(".mp4", "")
        name += '.60x.avi'
        if not os.path.exists(temp_time_elapse_video_dir):
            os.makedirs(temp_time_elapse_video_dir)
        fn = os.path.join(temp_time_elapse_video_dir, name)
        data_obj['elapse_60x_fn'] = fn
        if os.path.exists(fn):
            util.safe_os_remove(fn)
        videoWriter = cv2.VideoWriter(fn, 
            cv2.VideoWriter_fourcc('I', '4', '2', '0'), 
            data_obj['fps'], 
            (data_obj['width'],data_obj['height']))
        data_obj['elapse_60x'] = videoWriter
    if data_obj['frame_idx'] % 60 < 3:
        frames_elapse.append(data_obj['frame'])
    if data_obj['frame_idx'] % 60 == 3:
        m = get_recent_avg_img(frames_elapse)
        frames_elapse = []
        logger.info("write one frame fox 60x elapse video, frame_idx:" + str(data_obj['frame_idx']))
        data_obj['elapse_60x'].write(m)

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





def ffmpg_split(start_time, end_time, segment, input_file, diff_frames_by_index):
    temp_dir = "temp"
    assert os.path.exists(temp_dir)

    # generate final splitted meteor video
    t = get_record_time_from_video_name(input_file, start_time)
    date = t.strftime("%Y%m%d")
    out_file = t.strftime("%Y%m%d_%H%M%S.mp4")
    local_file = os.path.join(temp_dir, out_file)
    remote_dir = os.path.join(cfg['base_output_path'], date)
    remote_file = os.path.join(remote_dir, out_file)
    if os.path.exists(local_file):
        util.safe_os_remove(local_file)
    cmd = 'ffmpeg -ss "{0}" -t "{1}" -i "{2}" -vcodec copy -acodec copy "{3}" 2>&1 '.format(
            start_time, end_time, input_file, local_file)

    logger.info("run ffmpeg, cmd: " + cmd)
    text = os.popen(cmd).read()
    logger.info("cmd ret: " + text)
    if local_file != remote_file:
        # upload splitted video to remote output path
        store_lib.store_file_to_output_path(local_file, remote_file)
        util.safe_os_remove(local_file)

    # generate GIF file for debug
    logger.info("generate gif file.  segment: " + str(segment))
    gif_file_name = t.strftime("%Y%m%d_%H%M%S_diff.gif")
    local_gif_file_path = os.path.join(temp_dir, gif_file_name)
    remote_gif_file_path = os.path.join(remote_dir, gif_file_name)
    temp_frames = []
    for idx in range(segment[0], segment[1] + 1):
        logger.info("try to find diff frames , idx: " + str(idx))
        if str(idx) in diff_frames_by_index:
            temp_frames.append(diff_frames_by_index[str(idx)])
    if len(temp_frames) > 0:
        duration_sec = int(len(temp_frames)/3)
        if duration_sec < 3:
            duration_sec = 3
        logger.info("gif duration: " + str(duration_sec))
        logger.info("local gif file: " + local_gif_file_path)
        logger.info("target gif file: " + remote_gif_file_path)
        imageio.mimsave(local_gif_file_path, temp_frames, 'GIF', duration=duration_sec)
        if local_gif_file_path != remote_gif_file_path:
            store_lib.store_file_to_output_path(local_gif_file_path, remote_gif_file_path)
            logger.info("safe remove local gif file: " + local_gif_file_path)
            util.safe_os_remove(local_gif_file_path)

def get_record_time_from_video_name(full_path, shift_time):
    basename = os.path.basename(full_path)
    t = datetime.datetime.strptime(basename, "WIN_%Y%m%d_%H_%M_%S_Pro.mp4")
    shift_hour = shift_time.split(":")[0]
    shift_min = shift_time.split(":")[1]
    shift_sec = shift_time.split(":")[2]
    seconds = int(shift_hour) * 3600 + int(shift_min) * 60 + int(shift_sec)
    t2 = t + datetime.timedelta(seconds = seconds)
    return t2
    

#def test_get_record_time():
#    p = os.path.join(input_file_base_path, 'WIN_20220514_04_54_56_Pro.mp4')
#    t = get_record_time_from_video_name(p, '00:00:01')
#    assert '2022-05-14 04:54:57' == t.strftime("%Y-%m-%d %H:%M:%S")
#    p = os.path.join(input_file_base_path, 'WIN_20220514_04_54_56_Pro.mp4')
#    t = get_record_time_from_video_name(p, '00:09:01')
#    assert '2022-05-14 05:03:57' == t.strftime("%Y-%m-%d %H:%M:%S")
#    p = os.path.join(input_file_base_path, 'WIN_20220514_04_54_56_Pro.mp4')
#    t = get_record_time_from_video_name(p, '01:09:01')
#    assert '2022-05-14 06:03:57' == t.strftime("%Y-%m-%d %H:%M:%S")






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
    #logger.info("get_segments_from_index entry, index: ", index)
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
    #logger.info("get segment return , segments: ", segments)
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
    logger.info("[merge segments] segments input: %s", segments)
    last_begin = -1
    last_end = -1
    out_segments = []
    if len(segments) == 0:
        return out_segments
    # if distance between 2 segments is too near, then merge them
    for seg in segments:
        begin, end = seg
        if last_end == -1:
            last_begin = begin
            last_end = end 
        # calc distance
        else:
            if begin - last_end < 5 * fps:
                last_end = end
            else:
                logger.info("[merge segments] 11111 one segment lenth: %d,  from %d to %d",  last_end - last_begin, last_begin, last_end)
                out_segments.append([last_begin, last_end])
                last_begin = begin
                last_end = end
    if segments[-1][1] == last_end:
        logger.info("[merge segments] 22222 one segment lenth: %d,  from %d to %d",  last_end - last_begin, last_begin, last_end)
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

def calc_split_range(index, frame_count, fps, time_sec, data_obj):
    l = prefix_video_sec
    # first find multiple segment
    segments = get_segments_from_index(index)
    # then merge near segments
    new_segments = merge_segments(segments, fps)
    param_list = []
    data_obj['filter_segments'] = []
    for seg in new_segments:
        seg_len = seg[1] - seg[0]
        logger.info("[calc split range] seg_len: %d,  seg: %s", seg_len, seg)
        if seg_len < 2:
            msg = "[filter segment] reason: single diff frame. seg: " + str(seg)
            logger.info(msg)
            data_obj['filter_segments'].append(msg)
            continue
        begin_time, duration = calc_begin_time_and_duration(seg, fps)
        begin_time_hum = seconds_to_hum_readable(begin_time)
        duration_hum = seconds_to_hum_readable(duration)
        param_list.append([begin_time_hum, duration_hum, seg])
    return param_list


def get_local_path(full_path):
    fn = os.path.basename(full_path)
    return os.path.join("temp", fn)

def fetch_video(full_path):
    if not os.path.exists("temp"):
        try:
            os.makedirs("temp")
        except:
            logger.info(traceback.format_exc())
    local_f = get_local_path(full_path)
    if os.path.exists(local_f):
        util.safe_os_remove(local_f)
    store_lib.fetch_file_from_input_path(
        full_path, local_f)
    
    
def process_one_video(full_path):
    logger.info("processing video, " + full_path)
    t11 = time.time()
    fetch_video(full_path)
    t22 = time.time() 
    local_file = get_local_path(full_path)
    t1 = time.time()
    ret = read_one_video(local_file, full_path)
    t2 = time.time()
    if ret == None:
        return
    index = ret['index']
    frame_count = ret['frame_count']
    fps = ret['fps']
    time_sec = ret['time_sec']
    filter_info_list = ret['filter_info_list']
    if len(index) > 0 and cfg['DEBUG'] == 0:
        process_speed = int(frame_count / (t2-t1))
        param_list = calc_split_range(index, frame_count, fps, time_sec, ret)
        if len(param_list) > 0:
            for param in param_list:
                ffmpg_split(param[0], param[1], param[2], local_file, ret["diff_frames_by_index"])
    logger.info("process time: " + str(int(t2-t1)))
    time_use = t2-t1
    process_speed = int(frame_count/time_use)
    logger.info("process speed fps: " + str(int(frame_count/(t2-t1))))
    d = {}
    d["IP"] = cfg['IP_ADDR']
    d["index"] = index
    d["index_with_rec"] = ret['index_with_rec']
    if 'filter_segments' in ret:
        d['filter_segments'] = ret['filter_segments']
    d["process_speed_fps"] = process_speed
    d['fetch_time_sec'] = int(t22 - t11)
    d['analyze_video_time_sec'] = int(time_use)
    d['video_length_sec'] = int(time_sec)
    d['filter_info_list'] = filter_info_list
    text = json.dumps(d, ensure_ascii=False, indent=2)
    write_analyze(full_path, text)
    util.safe_os_remove(local_file)


def write_analyze(full_path, text):
    ana_file = full_path + '.analyze'
    logger.info("try to create .analyze file, path: " + ana_file)
    
    if cfg['DEBUG']:
        logger.info("analyze result:\n" + text)
    else:
        store_lib.write_file_to_input_path(
            full_path + '.analyze',
            text.encode("utf-8")
        )

def test_write_analyze_file():
    full_path = "1.mp4"
    write_analyze(full_path, 'text content')
    time.sleep(0.1)
    assert store_lib.input_path_file_exists("1.mp4.analyze")
    with open("1.mp4.analyze") as f1:
        text = f1.read()
    store_lib.delete_input_path_file("1.mp4.analyze")

