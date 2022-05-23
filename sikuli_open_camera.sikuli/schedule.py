#encoding=utf-8
import time
import datetime
import os
import sys
import json
import traceback

from astral import LocationInfo
from astral.sun import sun
import psutil

# 说明：
# --forceRecord 强制录像

# 录制时间，单位秒
RECORD_TIME = 200
START_TIME = '2300'
END_TIME = '0500'
MAX_VIDEO_SUM_SIZE = 45 * 1024 * 1024 * 1024
video_local_dir = r'E:\video\camera'



def read_sunset_sunrise_time():
    global START_TIME, END_TIME
    city = LocationInfo(('Beijing', 'China',  39.92, 116.46, 'Asia/Shanghai', 0))
    s = sun(city.observer, date=datetime.date.today(), tzinfo=city.timezone)
    sunrise=s['sunrise']
    sunset=s['sunset']
    myPrint("sunrise: " + str(sunrise))
    myPrint("sunset: " + str(sunset))
    a = sunset + datetime.timedelta(seconds = 600) 
    START_TIME = a.strftime("%H%M")
    b = sunrise - datetime.timedelta(seconds = 1800)
    END_TIME = b.strftime("%H%M")
    myPrint("START_TIME: " + START_TIME + "  END_TIME: " + END_TIME)


def is_hit_sum_size_limit():
    li = os.listdir(video_local_dir)
    sum = 0
    for f in li:
        full_p = os.path.join(video_local_dir, f)
        if os.path.exists(full_p):
            sum += os.path.getsize(full_p)
    myPrint("current size: " + str(sum/1024/1024) + " MB")
    if sum > MAX_VIDEO_SUM_SIZE:
        myPrint("hit max limit")
        return True
    else:
        return False
    
def myPrint(s):
    n = datetime.datetime.now()
    print("[" + str(n) + "] " + s)


def make_done_file():
    v_list = os.listdir(video_local_dir)
    v_list = [x for x in v_list if x.endswith(".mp4")]
    v_list.sort()
    for v in v_list:
        full_p_done = os.path.join(video_local_dir, v + '.done')
        if not os.path.exists(full_p_done):
            with open(full_p_done, 'w') as f2:
                f2.write(" ")

def should_record():
    for arg in sys.argv:
        if '--forceRecord' in arg:
            return True
    n = datetime.datetime.now()
    hourMin = n.strftime("%H%M")
    myPrint("current time: " + hourMin)
    if hourMin > START_TIME and hourMin < '2359':
        myPrint("should record is True")
        return True
    if hourMin > '0000' and hourMin < END_TIME:
        myPrint("should record is True")
        return True
    myPrint("should record is False")
    return False

def send_cmd(cmd_list):
    myPrint("send cmd: " + str(cmd_list))
    with open("op.json", 'w') as f1:
        f1.write(json.dumps(cmd_list))
    ret = os.popen("java -jar sikulixide-2.0.5.jar -r sikuli_open_camera.sikuli 2>&1").read()
    myPrint("sikuli ret: " + ret)


def is_camera_process_exists():
    for proc in psutil.process_iter():
        # Get process detail as dictionary
        pInfoDict = proc.as_dict(attrs=['pid', 'name', 'cpu_percent'])
        if 'Camera' in pInfoDict['name'] or 'camera' in pInfoDict['name']:
            myPrint("found camera process: " + str(pInfoDict))
            return True
    return False

def loop_process():
    read_sunset_sunrise_time()
    if is_camera_process_exists():
        send_cmd(["try_close_camera"])
    cnt = 0
    while 1:
        if is_hit_sum_size_limit() == False and should_record(): 
            send_cmd(["stop_record", "start_record"])
            time.sleep(RECORD_TIME)
            make_done_file()
        else:
            if is_camera_process_exists():
                send_cmd(["try_close_camera"])
            time.sleep(60)
        cnt += 1
        myPrint("global iter num: " + str(cnt))

    # 退出时，尝试关闭camera
    if is_camera_process_exists():
        send_cmd(["try_close_camera"])

if __name__ == "__main__":
    loop_process()

