
ps aux | grep python | grep ftp_server.py 

CNT=`ps aux | grep python | grep ftp_server.py | wc -l`

if [ $CNT -eq 0 ]; then
    nohup ./venv/bin/python ftp_server.py &
fi

