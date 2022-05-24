#encoding=utf-8
import time
import datetime
import os
import sys
import json
import traceback

# 录制时间，单位秒
RECORD_TIME = 150
START_TIME = '2300'
END_TIME = '0500'
MAX_VIDEO_SUM_SIZE = 45 * 1024 * 1024 * 1024
video_local_dir = r'E:\video\camera'

def read_sunset_sunrise_time():
    global START_TIME, END_TIME
    myPrint("try get sunrise sunset time")
    current_month = datetime.datetime.now().strftime("%m")
    idx = int(current_month) - 1
    s =  get_sunrise_time(idx)
    myPrint("s: " + str(s))
    s0 = datetime.datetime.strptime(s[1], "%H%M") + datetime.timedelta(seconds=3600)
    s1 = datetime.datetime.strptime(s[0], "%H%M") - datetime.timedelta(seconds=3600)
    START_TIME = s0.strftime("%H%M")
    END_TIME = s1.strftime("%H%M")
    myPrint("START_TIME: " + START_TIME + "  END_TIME: " + END_TIME)

def get_sunrise_time(idx):
    li = [["0733", "1713"], ["0707", "1749"], ["0625", "1820"], ["0536", "1852"],
          ["0456", "1923"], ["0445", "1944"], ["0458", "1942"], ["0526", "1911"],
          ["0555", "1824"], ["0624", "1735"], ["0659", "1658"], ["0728", "1650"]]
    s = li[idx]
    return s


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

def start_camera():
    wait(1)
    
    if exists("1652014299798.png"):
        click("1652014190576.png")
    else: 
        if exists("1652014232416.png"):
            click("1652014232416.png")

def try_click_start_button():
    time.sleep(1)
    try:
        wait("1652015554359.png")
    except:
        myPrint("wait start button failed")
    time.sleep(1)
    if exists("1652015554359.png"):
        try:
            click(Pattern("1652015554359.png").similar(0.64))
            myPrint("start done, then return")
            return True
        except:
            pass
    myPrint("click start button failed")
    time.sleep(1)
    return False
        
def start_record():
    myPrint("start record")
    ret = try_click_start_button()
    if ret == False:
        ret = try_click_start_button()
        if ret == False:
            # 可能是camera没启动   
            print("can not find record button. try to start camera")
            start_camera()
            myPrint("start OK, now try to start record")
            ret = try_click_start_button()
            if ret == False:
                ret = try_click_start_button()
                if ret == False:
                    myPrint("after retry and retry, still cannot click start button")
               
def stop_record():
    myPrint("try to stop record")
    if exists("1652015879422.png"):
        click("1652015879422.png")
        myPrint("stop done, then return")
        time.sleep(1)
        return
    else:
        myPrint("can not find stop record button, now retry")
        time.sleep(4)
        if exists("1652015879422.png"):
            click("1652015879422.png")
            time.sleep(1)

def switch_video():
    pass

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
    n = datetime.datetime.now()
    myPrint("current n: " + str(n))
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

def wait_util_stop():
    cnt = 0
    while cnt < RECORD_TIME:
        cnt += 1
        time.sleep(1)
        if cnt %30 == 1:
            myPrint("waiting, cnt: " + str(cnt))
    # stop record
    myPrint("wait end, now try to stop record") 
    stop_record()
    make_done_file()

def try_close_camera():
    myPrint("try to close camera")
    wait(1)
    if exists("1653186710812.png"): 
        click(Pattern("1653186710812.png").targetOffset(169,-31))
        myPrint("close Done")
    myPrint("close camera return")

def read_commands():
    cmd_list = []
    if os.path.exists('op.json'):
        try:
            f = open('op.json')
            txt = f.read()
            f.close()
            cmd_list = json.loads(txt)
            os.remove('op.json')
        except:
            traceback.print_exc()
            
    return cmd_list

def execute_cmd(cmd_list):
    for cmd in cmd_list:
        if cmd == "start_record":
            start_record()
        if cmd == "stop_record":
            stop_record()
        if cmd == "try_close_camera":
            try_close_camera()
    

def loop_process(): 
    cnt = 0
    while 1:
        read_sunset_sunrise_time()
        if is_hit_sum_size_limit() == False and should_record(): 
            start_record()
            wait_util_stop()    
        else:
            try_close_camera()
            myPrint("sleep 60")
            time.sleep(60)
        cnt += 1
        myPrint("global iter num: " + str(cnt))
        # 调试时，打开以下注释
        #if cnt > 2:
        #    break
    # 退出时，尝试关闭camera
    try_close_camera()

def main():
    cmd_list = read_commands()
    if len(cmd_list) > 0:
        execute_cmd(cmd_list)
    else:
        loop_process()

main()
