# -*- coding: utf-8 -*-
# @Author   : xudong


from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer
from pyftpdlib.authorizers import DummyAuthorizer

from logzero import logger

import parse_config
cfg = parse_config.parse()

def run_server():
    logger.info("start ftp server, root path:" + cfg['FTP_BASE_DIR'])    
    authorizer = DummyAuthorizer()
    authorizer.add_user('admin', '123456',
                        cfg['FTP_BASE_DIR'],
                        perm='elradfmwM')
    handler = FTPHandler
    handler.authorizer = authorizer

    server = FTPServer(('0.0.0.0', 8021), handler)
    server.serve_forever()
