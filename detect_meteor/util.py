import os
import traceback
from logzero import logger


def safe_os_remove(full_path):
    if os.path.exists(full_path):
        try:
            os.remove(full_path)
        except:
            msg = traceback.format_exc()
            logger.warn("error when try remove: " + msg)

