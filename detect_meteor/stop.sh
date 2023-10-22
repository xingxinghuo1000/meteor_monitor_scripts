set -x

ps aux| grep python3 | grep offline_detect_from_mp4.py | awk '{print $2}'  | xargs kill
ps aux| grep ffmpeg 
ps aux| grep ffmpeg | awk '{print $2}'  | xargs kill
sleep 0.5

