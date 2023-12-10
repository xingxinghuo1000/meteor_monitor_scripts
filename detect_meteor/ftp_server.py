# -*- coding: utf-8 -*-
# @Author   : xudong


from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer
from pyftpdlib.authorizers import DummyAuthorizer
import util
from logzero import logger

import parse_config
cfg = parse_config.parse()

port_start = 8021

def run_server():
    logger.info("start ftp server, root path:" + cfg['FTP_BASE_DIR'])    
    authorizer = DummyAuthorizer()
    authorizer.add_user('admin', '123456',
                        cfg['FTP_BASE_DIR'],
                        perm='elradfmwM')
    handler = FTPHandler
    handler.authorizer = authorizer
    port = port_start
    try_cnt = 0
    while util.is_port_connect(port):
        port += 1
        try_cnt += 1
        if try_cnt > 10:
            break
    if try_cnt > 10:
        # too may retries to find one port, then skip
        logger.info("too may retries to find one port, then skip")
    else:
        logger.info("ftp server, try to listen port: %d", port)
        server = FTPServer(('0.0.0.0', port), handler)
        server.serve_forever()
