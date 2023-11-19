set -x

ps aux| grep python3 | grep detect_meteor.py | awk '{print $2}'  | xargs kill
ps aux| grep ffmpeg 
ps aux| grep ffmpeg | awk '{print $2}'  | xargs kill
sleep 0.5

