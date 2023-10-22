set -x

ps aux| grep python | grep offline_detect_from_mp4.py

CNT=`ps aux | grep python | grep offline_detect_from_mp4.py | wc -l`

if [ $CNT -eq 0 ]; then
  sh offline_detect_from_mp4.sh
fi

