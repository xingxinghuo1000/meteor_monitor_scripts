import sys
import os
import shutil
import time
import datetime
import logzero
from logzero import logger
import flask
from flask import Flask, render_template, request
import requests
import threading
import json
import util
import parse_config
import process_video_worker as pvw


if not os.path.exists("logs"):
    os.makedirs("logs")
logzero.logfile("logs/log-default.log", maxBytes=10 * 1024 * 1024, backupCount=5)


import capture_by_ffmpeg as cap
import ftp_server

cfg = parse_config.parse()



app = Flask(__name__)



@app.route('/index', methods=['GET'])
def register():
    return render_template('index.html')

    

if __name__ == "__main__":
    assert True == cap.check_ffmpeg()
    #assert True == util.check_python_bin()

    t2 = threading.Thread(target=util.loop_clean_temp_dir)
    t2.daemon = True
    t2.start()


    if cfg['CAPTURE_VIDEO_FLAG']:
        # loop process or capture video
        cap.init_capture()

    t5 = threading.Thread(target=pvw.loop_process_video)
    t5.daemon = True
    t5.start()

    logger.info("ENABLE_FTP_SERVER: %d", cfg['ENABLE_FTP_SERVER'])
    if cfg['ENABLE_FTP_SERVER'] == 1:
        logger.info("start ftp server thread")
        t6 = threading.Thread(target = ftp_server.run_server)
        t6.daemon = True
        t6.start()

    t7 = threading.Thread(target = cap.cap_loop)
    t7.daemon = True
    t7.start()


    app.run(port=cfg['SERVER_PORT'])

