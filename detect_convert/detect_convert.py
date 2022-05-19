#encodings=utf-8
import os
import sys
import datetime
import time
import traceback

# 全局配置 是否删除老的原始视频
delete_orig_video = True

# 是否合成每月的合集
combine_month_suite = True

# True：仅在白天转码
# 如果设置为False，则夜间会实时转码
only_process_on_sunrise = True

# 是否发送钉钉通知
send_ding_alert = False
# 钉钉token
ding_token = '11111'


# 合成每月合集的时机，是在下个月的任意一天，如果发现上个月没有合集文件
# 则尝试使用上个月的所有视频，合成一个视频，首先使用无损的，如果没有
# 则使用mp4文件合成

# 如果有误报，例如发现了飞虫，鸟类等视频，可以手工删除，然后删除掉对应的
# mp4文件，想重新生成上个月的合集，则删掉即可，后续会自动重新生成
# 想重新生成昨日合集，则删掉即可，会自动重新生成

# 重新生成，会扫描上个月1日到今天的视频，今天的视频，如果生成时间与
# 当前时间相差小于60秒，则不转换
# 合并视频，今天的目录，不处理，如果是昨天的目录，要判断当前是否小于上午8点
# 8点之前，不合并视频，8点以及以后，则合并

src_dir = os.getcwd()


def get_last_month():
    current_day = datetime.datetime.now().day
    #print("current_day: ", current_day)
    last_month_t = datetime.datetime.now() - datetime.timedelta(days = current_day)
    last_month = last_month_t.strftime("%Y%m")
    return last_month

def get_current_month():
    return datetime.datetime.now().strftime("%Y%m")   

def get_months():
    years = os.listdir(src_dir)
    years = [x for x in years if os.path.isdir(x)]
    print("years: ", years)
    process_months = []
    last_month = get_last_month()
    current_month = get_current_month()
    print("last month: ", last_month)
    print("current month: ", current_month)
    out = []
    for year in years:
        year_dir = os.path.join(src_dir, year)
        months = os.listdir(year_dir)
        print("months:", months)
        for  month in months:
            if month in [last_month, current_month]:
                out.append(os.path.join(year_dir, month))
    return out

def get_dirs():
    months = get_months()
    print("months:", months)
    days_out = []
    for month_path in months:
        dirs = os.listdir(month_path)
        for d in dirs:
            days_out.append(os.path.join(month_path, d))
    return days_out

def process_recent_days(dirs):
    for d in dirs:
        process_one_day_dir(d)

def should_process_video(path):
    print("is_video, path: ", path)
    ext = os.path.splitext(path)[-1]
    if ext not in ['.avi']:
        print("not video, then skip, ext is: ", ext)
        return False
    fsize = 0
    try:
        fsize = os.path.getsize(path)
    except:
        traceback.print_exc()
        
    print("file size: ", fsize)
    if fsize < 1024*1024:
        print("file size too small, then skip")
        return False
    f_name = os.path.basename(path)
    time_str = f_name.split("_")[0] + "_" + f_name.split("_")[1]
    time_str = time_str[1:]
    assert len(time_str) == 15
    print("time str: ", time_str)
    file_time = datetime.datetime.strptime(time_str, "%Y%m%d_%H%M%S")
    now_time = datetime.datetime.now()
    delta = now_time - file_time
    sec = delta.seconds
    print("delta seconds: ", sec, " delta: ", delta)
    if sec < 10:
        print("sec < 10, then skip")
        return False
    return True


def process_one_day_dir(d):
    video_list = os.listdir(d)
    video_list = [os.path.join(d,x) for x in video_list]
    video_list = [x for x in video_list if should_process_video(x)]
    for  video in video_list:
        convert_one_video(video)
    merge_one_day_video(d)

def merge_one_day_video(d):
    base_name_dir = os.path.basename(d)
    yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
    today_str = datetime.datetime.now().strftime("%Y%m%d")
    if today_str == base_name_dir:
        print("skip today dir")
        return
    yesterday_str = yesterday.strftime("%Y%m%d")
    if yesterday_str == base_name_dir:
        print("dir is yesterday")
        current_hour = datetime.datetime.now().strftime("%H")
        if int(current_hour) < 8:
            print("current hour < 8, then skip")
            return
    # ffmpeg -i "concat:f00282urkwd.321002.1.ts|f00282urkwd.321002.2.ts|f00282urkwd.321002.3.ts|f00282urkwd.321002.4.ts|f00282urkwd.321002.5.ts|f00282urkwd.321002.6.ts|f00282urkwd.321002.7.ts|f00282urkwd.321002.8.ts|f00282urkwd.321002.9.ts|f00282urkwd.321002.10.ts|f00282urkwd.321002.11.ts|f00282urkwd.321002.12.ts|f00282urkwd.321002.13.ts|f00282urkwd.321002.14.ts|f00282urkwd.321002.15.ts|f00282urkwd.321002.16.ts|f00282urkwd.321002.17.ts|" -c copy output.mp4
    merge_output = os.path.join(d, "merge-" + os.path.basename(d) + ".mp4")
    if os.path.exists(merge_output):
        print("merge  video exists, then return")
        return
    mp4_list = [os.path.join(d,x) for x  in os.listdir(d) if x.endswith(".mp4")]
    if len(mp4_list) == 0:
        print("no mp4 found, then return")
        return
    file_list_file = os.path.join(d, 'filelist.txt')
    with open(file_list_file, 'w') as f1:
        for mp4 in mp4_list:
            f1.write("file '{0}'\n".format(mp4))
    cmd = r'''ffmpeg -f concat -safe 0 -i {0} -c copy {1}'''.format(
        file_list_file, merge_output
    )
    print("cmd: ", cmd)
    os.system(cmd)

def try_delete_avi(path):
    if delete_orig_video == True and os.path.exists(path):
        print("try  to remove origin video")
        try:
            os.remove(path)
        except:
            print("remove orgin video error")

def convert_one_video(path):
    dir_name = os.path.dirname(path)
    file_name = os.path.basename(path)
    ext = os.path.splitext(file_name)[-1]
    prefix = file_name.replace(ext, "")
    mp4_file = os.path.join(dir_name, prefix + '.mp4')
    # 如果已经存在，尝试删除
    if os.path.exists(mp4_file):
        print("already has mp4 file: {0}, then skip".format(
            os.path.basename(mp4_file)))
        try_delete_avi(path)
    cmd = r'''ffmpeg -i "{0}"  -c:v h264_qsv -b 8000k -strict -2  "{1}"'''.format(
        path, mp4_file)
    print("cmd: ", cmd)
    os.system(cmd)
    # 转换完毕，尝试删除
    if os.path.exists(mp4_file):
        print("already has mp4 file: {0}, then skip".format(
            os.path.basename(mp4_file)))
        try_delete_avi(path)



def process_last_month_data():
    last_month = get_last_month()
    current_month = get_current_month()
    print("last month: ", last_month)
    print("current month: ", current_month)
    if last_month == current_month:
        print("[process_last_month_data] error, will skip process last month")



def main_loop():
    while 1:
        current_minute = datetime.datetime.now().strftime("%H:%M")
        print("current time: ", datetime.datetime.now())
        print("current_minute: ", current_minute)
        #  夜间直接跳过，不处理
        #  这里有个开关控制，如果only_process_on_sunrise为False
        #  则夜间也可以实时处理
        if only_process_on_sunrise == True and current_minute > "18:00":
            time.sleep(10)
            continue
        # 过了凌晨0点后，不处理，上午7点半后，再处理
        if current_minute < "07:30":
            time.sleep(1)
            continue
        print("begin process_all")    
        process_all()
        print("now sleep 60 sec")
        time.sleep(60)

def process_all():
    print('source cwd: ', src_dir)
    dirs = get_dirs()
    print("will process dirs: ", dirs)
    process_recent_days(dirs)
    process_last_month_data()
    


if __name__ == '__main__':
    main_loop()


    
