# -*- coding: utf-8 -*-
# @Author   : xudong


from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer
from pyftpdlib.authorizers import DummyAuthorizer

def run_server(base_path):

    authorizer = DummyAuthorizer()
    authorizer.add_user('admin', '123456',
                        base_path,
                        perm='elradfmwM')
    handler = FTPHandler
    handler.authorizer = authorizer

    server = FTPServer(('0.0.0.0', 8021), handler)
    server.serve_forever()
