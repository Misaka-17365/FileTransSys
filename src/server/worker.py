
from socket import socket
from queue import Queue
from threading import Thread
from concurrent.futures import ThreadPoolExecutor

from ..defs import UserInfo

class Worker(Thread):
    '''
    Worker线程时处理客户端请求的线程

    客户端连接到服务器时，监听socket返回一个已经建立连接的 `socket` ，

    使用该`socket`实例化Worker线程，即这个Worker线程负责处理这个`socket`后面的客户端的请求
    '''
    def __init__(self, queue:Queue, socket:socket):
        self.queue = queue
        self.socket = socket
        self.userinfo:UserInfo = None
        self.is_login = False

        self.pool = ThreadPoolExecutor(6, 'File Block Trans')
        return
    
    def run(self):
        ...


    def stop(self):
        ...