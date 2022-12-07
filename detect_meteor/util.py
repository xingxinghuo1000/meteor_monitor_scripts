import os
import traceback


def safe_os_remove(full_path):
    try:
        os.remove(full_path)
    except:
        traceback.print_exc()


