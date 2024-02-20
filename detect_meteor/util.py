import os
import traceback
import socket
import time
import datetime
import traceback
from suntime import Sun, SunTimeException
from logzero import logger
import parse_config

cfg = parse_config.parse()

def safe_os_remove(full_path):
    if os.path.exists(full_path):
        try:
            os.remove(full_path)
        except:
            msg = traceback.format_exc()
            logger.warn("error when try remove: " + msg)

def is_port_connect(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.settimeout(0.2)
            s.connect(('127.0.0.1', port))
        except Exception:
            # 建联失败
            return False
        s.close()
        return True

def is_port_open(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('localhost', port))
            logger.info("port %d  is usable ", port)
            return True
        except:
            logger.info("bind port error: %s", traceback.format_exc())
            return False


def get_sun_time(latitude, longitude):
    assert type(latitude) == type(1.1)
    assert type(longitude) == type(1.1)
    sun = Sun(latitude, longitude)
    today_sr_utc = sun.get_sunrise_time()
    today_ss_utc = sun.get_sunset_time()
    today_sr_local = utc2local(today_sr_utc)
    today_ss_local = utc2local(today_ss_utc)
    logger.info("today_sr_utc: " + str(today_sr_utc))
    logger.info("today_ss_utc: " + str(today_ss_utc))
    logger.info("today_sr_local: " + str(today_sr_local))
    logger.info("today_ss_local: " + str(today_ss_local))
    return today_sr_utc, today_ss_utc, today_sr_local, today_ss_local

    
def utc2local(utc_dtm):
    local_tm = datetime.datetime.fromtimestamp( 0 )
    utc_tm = datetime.datetime.utcfromtimestamp( 0 )
    offset = local_tm - utc_tm
    return utc_dtm + offset

def local2utc(local_dtm):
    return datetime.datetime.utcfromtimestamp( local_dtm.timestamp() )



def is_night(n_str, a, b):
    if n_str >= "00:00" and n_str < a:
        return True
    if n_str > a and n_str < b:
        return False
    if n_str >= b and n_str <= "23:59":
        return True
    return False

def test_is_night():
    assert True == is_night("00:00", "05:00", "20:00")
    assert True == is_night("00:01", "05:00", "20:00")
    assert True == is_night("04:59", "05:00", "20:00")
    assert False == is_night("05:00", "05:00", "20:00")
    assert False == is_night("05:01", "05:00", "20:00")
    assert False == is_night("07:00", "05:00", "20:00")
    assert False == is_night("12:00", "05:00", "20:00")
    assert False == is_night("15:00", "05:00", "20:00")
    assert False == is_night("19:59", "05:00", "20:00")
    assert True == is_night("20:00", "05:00", "20:00")
    assert True == is_night("20:01", "05:00", "20:00")
    assert True == is_night("22:01", "05:00", "20:00")
    assert True == is_night("23:59", "05:00", "20:00")

def loop_clean_temp_dir():
    while 1:
        time.sleep(1)
        clean_temp_dir()
        time.sleep(600)


def clean_temp_dir():
    cur_time = time.time()
    if os.path.exists("temp"):
        logger.info("try to clean temp dir")
        for f in os.listdir("temp"):
            ff = os.path.join("temp", f)
            t = os.path.getmtime(ff)
            diff = int(cur_time - t)
            logger.info("(current time) - (temp time create time) = " + str(diff))
            if diff > 7200:
                logger.info("try to remove temp file: "+f)
                safe_os_remove(ff)


def should_process_now():
    n = datetime.datetime.now()
    n_str = n.strftime("%H:%M")
    delta2h = datetime.timedelta(hours=2)
    sr_utc, ss_utc, sr_local, ss_local = get_sun_time(float(cfg["LATITUDE"]), 
            float(cfg['LONGITUDE']))
    black_time_sr = sr_local - delta2h
    black_time_ss = ss_local + delta2h
    a = black_time_sr.strftime("%H:%M")
    b = black_time_ss.strftime("%H:%M")
    logger.info("now: " + n_str)
    logger.info("a: " + a + "     b: " + b)
    is_ni = is_night(n_str, a, b)
    logger.info("is_night: %d", is_ni)
    if is_ni:
        return False
    else:
        # is in daylight
        return True
    

def check_python_bin():
    assert cfg['PYTHON_BIN'] != ''
    bin_cmd = cfg['PYTHON_BIN']
    cmd = '%s --version' %(bin_cmd)
    ret = os.popen(cmd).read()
    assert 'Python 3' in ret
    return True



