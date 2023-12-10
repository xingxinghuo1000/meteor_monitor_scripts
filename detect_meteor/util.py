import os
import traceback
import socket
import datetime
import traceback
from suntime import Sun, SunTimeException
from logzero import logger


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





