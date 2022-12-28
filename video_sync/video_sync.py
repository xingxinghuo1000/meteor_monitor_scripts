import shutil
import os
import time
import traceback

video_path = r'D:\video\camera'
target_dir = r'U:\meteor_monitor\origin'
MAX_TARGET_VIDEO_SIZE = 60 * 1024 * 1024 * 1024


def delete_old_video():
    videos = os.listdir(target_dir)
    if len(videos) == 0:
        return
    videos = [x for x in videos if x.endswith('.mp4')]
    videos.sort()
    sum_size = sum_files_size(videos)
    print("sum size      : ", sum_size)
    print("sum size limit: ", MAX_TARGET_VIDEO_SIZE)
    while sum_size > MAX_TARGET_VIDEO_SIZE:
        os.remove(os.path.join(target_dir, videos[0]))
        done_file = os.path.join(target_dir, videos[0] + '.done')
        if os.path.exists(done_file):
            os.remove(done_file)
        lock_file = os.path.join(target_dir, videos[0] + '.lock')
        if os.path.exists(lock_file):
            os.remove(lock_file)
        analyze_file = os.path.join(target_dir, videos[0] + '.analyze')
        if os.path.exists(analyze_file):
            os.remove(analyze_file)
        time_elapse_file =  os.path.join(target_dir, videos[0].replace(".mp4", "")  + '.120x.mp4')
        if os.path.exists(time_elapse_file):
            os.remove(time_elapse_file)
        videos = os.listdir(target_dir)
        videos = [x for x in videos if x.endswith('.mp4')]
        videos.sort()
        sum_size = sum_files_size(videos)
        print("sum size      : ", sum_size)
        print("sum size limit: ", MAX_TARGET_VIDEO_SIZE)

def sum_files_size(file_list):
    s = 0 
    for f in file_list:
        full_p = os.path.join(target_dir, f)
        s += os.path.getsize(full_p)
    return s


def sync_one_video():
    delete_old_video()
    src_videos = os.listdir(video_path)
    src_videos = [x for x in src_videos if x.endswith('.mp4') and os.path.exists(os.path.join(video_path, x+'.done'))]
    src_videos.sort()
    print('found video list: ', src_videos)
    if len(src_videos) == 0:
        print("sleep 120")
        time.sleep(120)
        return
    one_video_path = os.path.join(video_path, src_videos[0])
    target_video = os.path.join(target_dir, src_videos[0])
    target_done = target_video + '.done'
    if os.path.exists(target_video):
        print("target video exists, first delete it")
        os.remove(target_video)
    print('copy file, from {0}, to {1}'.format(one_video_path, target_video))
    shutil.copy(one_video_path, target_video)
    with open(target_done, 'w') as f1:
        print('write done file')
        f1.write(" ")
    print('delete source video, ', one_video_path)
    os.remove(one_video_path)
    done_file = one_video_path + '.done'
    if os.path.exists(done_file):
        os.remove(done_file)
    


def main():
    while 1:
        try:
            sync_one_video()
            print('sleep 10')
            time.sleep(10)
        except:
            traceback.print_exc()
            print('sleep 5')
            time.sleep(5)


if __name__ == "__main__":
    main()
