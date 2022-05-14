import cv2
import os
import time
import pandas as pd

DEBUG = 1

def decode_fourcc(cc):
    return "".join([chr((int(cc) >> 8 * i) & 0xFF) for i in range(4)])

def convert_img(frame):
    resized = cv2.resize(frame,(512,512))
    gray_lwpCV = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    #cv2.imshow('Frame',gray_lwpCV)
    gray_lwpCV = cv2.GaussianBlur(gray_lwpCV, (5, 5), 0)
    #cv2.imshow('Frame',gray_lwpCV)
    return gray_lwpCV, resized


def read_one_video(full_path):
    split_limit = 600
    area_threh = 9
    thres1 = 20

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
    cnt = 0
    
    index = []
    images = []
    background = None
    t1  = time.time()
    last_cnt = 0
    while(vid_capture.isOpened()):
        ret, frame = vid_capture.read()
        if cnt %50 == 0:
            if cnt > 100:
                t2 = time.time()
                print("process speed, {0} frames per sec".format(int((cnt - last_cnt)/(t2-t1))))
                last_cnt = cnt
                t1 = t2
            print("frame count: ", cnt)
        if ret == True:
            match = 0
            # get background image, every 600 frames
            gray_lwpCV, resized_frame = convert_img(frame)
            if cnt % split_limit == 0:
                print("set background")
                background=gray_lwpCV
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
                    if (cv2.contourArea(c) < area_threh) | (cv2.contourArea(c) >int(512*512*0.8) ) :
                        continue
                    else:
                        (x, y, w, h) = cv2.boundingRect(c)
                        cv2.rectangle(resized_frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                        #cv2.imshow("rectangle", frame)
                        #print("find diff, frame index: ", cnt, ' rectangle: ', (x,y,w,h))
                        match = 1
                        index.append(cnt)
            if DEBUG:
                cv2.imshow("frame: ", resized_frame)
            if DEBUG:
                key = cv2.waitKey(50)
                if key == ord('q'):
                    break

        else:
            # read end, then break
            break
        cnt += 1
    vid_capture.release()


def main():
    #read_one_video("1.mp4")
    #read_one_video("meteor-2.mp4")
    read_one_video("meteor-3.mp4")

if __name__ == "__main__":
    main()

