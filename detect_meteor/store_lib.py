import ftplib
import os
import shutil
import parse_config
import traceback
import time
from logzero import logger

cfg = parse_config.parse()


def get_and_login_ftp_src():
    ftp = ftplib.FTP()
    ip = cfg['input_file_host'].split("/")[2].split(":")[0]
    port = cfg['input_file_host'].split(":")[2]
    ftp.connect(ip, int(port))
    ftp.login(cfg['input_file_user'],cfg['input_file_passwd'])
    return ftp

def get_and_login_ftp_dst():
    ftp = ftplib.FTP()
    ip = cfg['base_output_host'].split("/")[2].split(":")[0]
    port = cfg['base_output_host'].split(":")[2]
    ftp.connect(ip, int(port))
    ftp.login(cfg['base_output_user'],cfg['base_output_passwd'])
    return ftp



def fetch_file_from_input_path(remote_path, local_path):
    if cfg['input_file_type'] == 'ftp':
        remote_file_name = os.path.basename(remote_path)
        remote_dir = os.path.dirname(remote_path)
        ftp = get_and_login_ftp_src()
        ftp.cwd(remote_dir)
        file_handle = open(local_path, 'wb').write
        ftp.retrbinary("RETR " + remote_file_name, file_handle, 2048)
        ftp.quit()
        return {"code": 0}

    if cfg['input_file_type'] == 'local':
        shutil.copy(remote_path, local_path)
        return {"code": 0}

    return {"code": -1, "err_msg": "unknown type"}

def gen_local_temp_file():
    if not os.path.exists("temp"):
        try:
            os.makedirs("temp")
        except:
            logger.error(traceback.format_exc())
    file_name = os.path.join("temp", str(time.time()) + ".tmp")
    return file_name

def delete_input_path_file(remote_file):
    if cfg['input_file_type'] == 'ftp':
        remote_file_name = os.path.basename(remote_file)
        remote_dir = os.path.dirname(remote_file)
        ftp = get_and_login_ftp_src()
        ftp.cwd(remote_dir)
        ftp.delete(remote_file_name)
        ftp.quit()
        return {"code": 0}
    if cfg['input_file_type'] == 'local':
        os.remove(remote_file)
    return {"code": -1, "err_msg": "unknown type"}
    
def write_file_to_input_path(remote_file, byte_content):
    if cfg['input_file_type'] == 'ftp':
        tmp_file = gen_local_temp_file()
        f = open(tmp_file, 'wb')
        f.write(byte_content)
        f.close()
        store_file_to_input_path(tmp_file, remote_file) 
        os.remove(tmp_file)
        return
    if cfg['input_file_type'] == 'local':
        logger.info("write file to: %s", remote_file)
        f = open(remote_file, 'wb')
        f.write(byte_content)
        f.close()
        return
    assert False, "type is unknown"
    

def read_file_from_input_path(remote_file):
    if cfg['input_file_type'] == 'ftp':
        tmp_file = gen_local_temp_file()
        fetch_file_from_input_path(remote_file, tmp_file)
        f = open(tmp_file, 'rb')
        content = f.read()
        f.close()
        os.remove(tmp_file)
        return content
    if cfg['input_file_type'] == 'local':
        f = open(remote_file)
        content = f.read()
        f.close()
        return content
    assert False, "type is unknown"


def ftp_makedirs_cwd(ftp, path, first_call=True):
    try:
        ftp.cwd(path)
    except ftplib.error_perm:
        ftp_makedirs_cwd(ftp, os.path.dirname(path), False)
        ftp.mkd(path)
        if first_call:
            ftp.cwd(path)

def test_ftp_make_dirs_cwd():
    ftp = get_and_login_ftp_dst()
    ftp_makedirs_cwd(ftp, "/meteor_monitor/meteor_store/20221201", True)


def store_file_to_input_path(local_path, remote_path):
    if cfg['input_file_type'] == 'ftp':
        remote_file_name = os.path.basename(remote_path)
        remote_dir = os.path.dirname(remote_path)
        ftp = get_and_login_ftp_src()
        ftp_makedirs_cwd(ftp, remote_dir, True)
        file_handle = open(local_path, 'rb')
        ftp.storbinary("STOR " + remote_file_name, file_handle, 2048)
        ftp.quit()
        return {"code": 0}

    if cfg['input_file_type'] == 'local':
        remote_dir = os.path.dirname(remote_path)
        if not os.path.exists(remote_dir):
            os.makedirs(remote_dir)
        shutil.copy(local_path, remote_path)
        return {"code": 0}
    return {"code": -1, "err_msg": "unknown type"}



def store_file_to_output_path(local_path, remote_path):
    if cfg['base_output_type'] == 'ftp':
        remote_file_name = os.path.basename(remote_path)
        remote_dir = os.path.dirname(remote_path)
        ftp = get_and_login_ftp_dst()
        ftp_makedirs_cwd(ftp, remote_dir, True)
        file_handle = open(local_path, 'rb')
        ftp.storbinary("STOR " + remote_file_name, file_handle, 2048)
        ftp.quit()
        return {"code": 0}

    if cfg['base_output_type'] == 'local':
        remote_dir = os.path.dirname(remote_path)
        if not os.path.exists(remote_dir):
            os.makedirs(remote_dir)
        shutil.copy(local_path, remote_path)
        return {"code": 0}
    return {"code": -1, "err_msg": "unknown type"}


def list_input_path(remote_dir):
    if cfg['input_file_type'] == 'ftp':
        ftp = get_and_login_ftp_src()
        ftp.cwd(remote_dir)       
        lst = ftp.nlst()
        ftp.quit()
        return lst
    
    if cfg['input_file_type'] == 'local':
        return os.listdir(remote_dir)

    return None

def input_path_file_exists(remote_path):
    if cfg['input_file_type'] == 'ftp':
        remote_file_name = os.path.basename(remote_path)
        remote_dir = os.path.dirname(remote_path)
        ftp = get_and_login_ftp_src()
        ftp.cwd(remote_dir) 
        lst = ftp.nlst()
        ftp.quit()
        if remote_file_name in lst:
            return True
        else:
            return False

    if cfg['input_file_type'] == 'local':
        flag = os.path.exists(remote_path)
        logger.info("check file full path exists:  %s, return: %d", remote_path, flag)
        return flag

    assert False, "type is unknown"

    

