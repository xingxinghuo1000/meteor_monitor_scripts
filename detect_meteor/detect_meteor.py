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
import traceback
import threading
import uuid
import socket
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
    util.clean_temp_dir()
    if '--debug' in sys.argv:
        cfg['DEBUG'] = 1
    '''
    for arg in sys.argv:
        if '--video-file=' in arg:
            arg = arg.replace("--video-file=", "--video_file=")
        if '--video_file=' in arg:
            logger.info("process single video file")
            full_path = arg.split("--video_file=")[1]
            if full_path.startswith('"'):
                full_path = full_path.strip('"')
            store_lib.input_path_file_exists(full_path)
            logger.info("full_path: "+full_path)
            pov.process_one_video(full_path)
            sys.exit(0)
    '''

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

    t7 = theading.Thread(target = cap.cap_loop)
    t7.daemon = True
    t7.start()


    app.run()

