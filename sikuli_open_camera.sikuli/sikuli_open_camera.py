#encoding=utf-8
import time
import datetime
import os

# 录制时间，单位秒
RECORD_TIME = 150
START_TIME = '2300'
END_TIME = '0500'
MAX_VIDEO_SUM_SIZE = 45 * 1024 * 1024 * 1024
video_local_dir = r'E:\video\camera'

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
    if exists("1652018430575.png"): 
        click(Pattern("1652018430575.png").targetOffset(370,-23))
        myPrint("close Done")
    myPrint("close camera return")
    
def main():
    # first, try to stop, if recording
    stop_record()
    cnt = 0
    while 1:
        if is_hit_sum_size_limit() == False and should_record(): 
            start_record()
            wait_util_stop()    
        else:
            try_close_camera()
            time.sleep(60)
        cnt += 1
        myPrint("global iter num: " + str(cnt))
        # 调试时，打开以下注释
        #if cnt > 2:
        #    break
    # 退出时，尝试关闭camera
    try_close_camera()
    
main()
