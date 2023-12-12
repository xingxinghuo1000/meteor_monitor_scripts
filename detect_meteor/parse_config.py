import os
import sys
import uuid
import json
import time
import socket
from logzero import logger
import configparser


def get_local_ip():
    ip = ""
    try:
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)
    except:
        pass
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except:
        return None
    finally:
        s.close()
    return ip

def wait_get_local_ip():
    ip = get_local_ip()
    while ip == None:
        time.sleep(10)
        ip = get_local_ip()
    if ip == None:
        ip = str(uuid.uuid4())
    return ip

def read_config_text():
    text = ""
    if os.path.exists(".config"):
        f1 = open(".config")
        text = f1.read()
        f1.close()
    return text

cfg = {
}



first_call = 1

def parse():
    global first_call
    if first_call == 0:
        return cfg
    
    config = configparser.ConfigParser()
    config.read("config.ini", encoding="utf-8")



    cfg['IP_ADDR'] = wait_get_local_ip()
    logger.info("IP_ADDR: " + cfg['IP_ADDR'])
    cfg['LOCK_STR'] = str(uuid.uuid4())
 


    first_call = 0
    cfg['DEBUG'] = int(config.get("DEFAULT", "DEBUG", fallback="0"))
    cfg['EXECUTOR_NUM'] = int(config.get("DEFAULT", "EXECUTOR_NUM", fallback="1"))
    cfg['base_output_type'] = config.get("DEFAULT", "base_output_type", fallback="local")
    cfg['base_output_host'] = config.get("DEFAULT", "base_output_host", fallback="")
    cfg['base_output_user'] = config.get("DEFAULT", "base_output_user", fallback="admin")
    cfg['base_output_passwd'] = config.get("DEFAULT", "base_output_passwd", fallback="")
    cfg['base_output_path'] = config.get("DEFAULT", "base_output_path")

    cfg['input_file_type'] = config.get("DEFAULT", "input_file_type", fallback="local")
    cfg['input_file_host'] = config.get("DEFAULT", "input_file_host", fallback="")
    cfg['input_file_user'] = config.get("DEFAULT", "input_file_user", fallback="admin")
    cfg['input_file_passwd'] = config.get("DEFAULT", "input_file_passwd", fallback="")
    cfg['input_file_base_path'] = config.get("DEFAULT", "input_file_base_path")

    cfg['CAPTURE_VIDEO_PATH'] = config.get("DEFAULT", "CAPTURE_VIDEO_PATH")
    cfg['PYTHON_BIN'] = config.get("DEFAULT", "PYTHON_BIN")

    cfg['LATITUDE'] = float(config.get("DEFAULT", "LATITUDE"))
    cfg['LONGITUDE'] = float(config.get("DEFAULT", "LONGITUDE"))

    cfg['VIDEO_CAP_DIR_MAX_SIZE_BYTES'] = int(config.get("DEFAULT", "VIDEO_CAP_DIR_MAX_SIZE_BYTES"))

    cfg['DEVICE_NAME'] = config.get("DEFAULT", "DEVICE_NAME", fallback="")
    
    cfg['ENCODER'] = config.get("DEFAULT", "ENCODER")

    cfg['ALWAY_PROCESS'] = int(config.get("DEFAULT", "ALWAY_PROCESS", fallback="0"))
    cfg['RECORD_TIME_ELAPSE_VIDEO'] = int(config.get("DEFAULT", "RECORD_TIME_ELAPSE_VIDEO", fallback="0"))
    cfg['ENABLE_FTP_SERVER'] = int(config.get("DEFAULT", "ENABLE_FTP_SERVER", fallback="0"))
    cfg['FTP_BASE_DIR'] = config.get("DEFAULT", "FTP_BASE_DIR", fallback="")

    if cfg['ENABLE_FTP_SERVER']:
        assert cfg['FTP_BASE_DIR'] != ""

    logger.info("cfg: %s", json.dumps(cfg, indent=2, ensure_ascii=False))
    return cfg


