import os
import sys
import uuid
import time
import socket
from logzero import logger


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
    'DEBUG': 0,
    'EXECUTOR_NUM': 4,
    'base_output_type': 'local',
    'base_output_host': '',
    'base_output_user': 'pi',
    'base_output_passwd': '',
    'base_output_path': r'w:\meteor_monitor\meteor_store',
    'input_file_type': 'local',
    'input_file_host': '',
    'input_file_user': 'pi',
    'input_file_passwd': '',
    'input_file_base_path': r'w:\meteor_monitor\origin',
    'CAPTURE_VIDEO_PATH': r'w:\meteor_monit\origin',
    'IP_ADDR': '',
    'PYTHON_BIN': 'python',
    'LOCK_STR': '',
    'LATITUDE': 40,
    'LONGITUDE': 120,
    'VIDEO_CAP_DIR_MAX_SIZE_BYTES': 30 * 1024 * 1024 * 1024,
    'DEVICE_NAME': '',
    'ENCODER': '',
    'ALWAY_PROCESS': 0, 
}



first_call = 1

def parse():
    global first_call
    if first_call == 0:
        return cfg
    
    text = read_config_text()

    cfg['IP_ADDR'] = wait_get_local_ip()
    logger.info("IP_ADDR: " + cfg['IP_ADDR'])
    cfg['LOCK_STR'] = str(uuid.uuid4())
 
    for line in text.split("\n"):
        if line.startswith("#"):
            continue
        for k in cfg:
            if k in line:
                v = line.split("=")[1].strip(' "')
                cfg[k] = v
                print("resolve param from .config file, k:", k, "  v:", v)

    first_call = 0
    cfg['EXECUTOR_NUM'] = int(cfg['EXECUTOR_NUM'])
    cfg['DEBUG'] = int(cfg['DEBUG'])
    logger.info("cfg: %s", cfg)
    return cfg


