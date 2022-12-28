# -*- coding: utf-8 -*-
# @Author   : xudong


from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer
from pyftpdlib.authorizers import DummyAuthorizer

authorizer = DummyAuthorizer()
authorizer.add_user('admin', '123456',
                    'E:\\',
                    perm='elradfmwM')
handler = FTPHandler
handler.authorizer = authorizer

server = FTPServer(('0.0.0.0', 8021), handler)
server.serve_forever()
