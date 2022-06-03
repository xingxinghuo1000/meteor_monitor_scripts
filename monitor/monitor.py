import pyautogui as p
import datetime
import time
import os
import traceback
import shutil
import threading

interval = 2
max_file_num = 2000
save_path1 = 'img_record'
save_path2 = r'W:\meteor_monitor\img_record'

def screen_shot(save_path):
    if not os.path.exists(save_path):
        os.makedirs(save_path)
    n = datetime.datetime.now()
    s = n.strftime('%Y%m%d-%H%M%S.jpg')
    file_name = os.path.join(save_path, s) 
    tp=p.screenshot(file_name)
   

def delete_old_file(save_path):
    li = os.listdir(save_path)
    need_del_cnt = len(li) - max_file_num
    if need_del_cnt > 0:
        for i in range (need_del_cnt):
            ff = os.path.join(save_path, li[i])
            if os.path.exists(ff):
                os.remove(ff)
  
def main(save_path):
    cnt = 0
    while 1:
        cnt += 1
        time.sleep(interval)
        if cnt %10 == 0:
            try:
                delete_old_file(save_path)
            except:
                traceback.print_exc()
        try:
            screen_shot(save_path)
        except:
            traceback.print_exc()

if __name__ == "__main__":
    t1 = threading.Thread(target=main, args=(save_path1,), daemon=True)
    t1.start()
    #t2 = threading.Thread(target=main, args=(save_path2,), daemon=True)
    #t2.start()
    t1.join()
    #t2.join()
