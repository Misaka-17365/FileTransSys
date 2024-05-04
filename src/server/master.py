
from pathlib import Path
from socket import socket
from queue import Queue
from threading import Thread


from ..defs import UserInfo
from .worker import Worker

class ServerConfig:
    ...

class Th_listen(Thread):
    '''
    该线程仅进行监听,不进行监听之外的任何操作

    需要关闭该线程时,直接将监听的socket关闭,线程自动退出

    线程在退出前会向队列里写入一个空元组 (None, None)
    '''
    def __init__(self, socket:socket, queue:Queue):
        self.name = 'Connection Lisening'
        self.s = socket
        self.q = queue
        return
    
    def run(self):
        '''
        阻塞监听，将监听到的连接添加到队列中，送入 Master 线程

        当监听的socket出现意外时,不再进行监听,向队列写入空元组，线程自动退出
        '''
        while True:
            try:
                acp = self.s.accept()
                self.q.put(acp)
            except:
                break
        return
    
class Th_fileLoad(Thread):
    '''
    该线程负责将文件加载进内存，以提高多个用户下载同一个文件时文件传输速率，减少硬盘使用

    该线程实例化后自动运行

    当文件大小 > 2^28 (256MB) 时，不加载进内存
    '''
    def __init__(self, file:Path, file_map:dict[str, bytes]):
        self.name = 'File Loading'
        self.file_path = file
        self.file_map = file_map
        self.start()
        return
    
    def run(self):
        file_size = self.file_path.stat().st_size
        if file_size > 2**28:
            return
        with open(self.file_path, 'rb') as f:
            rbuf = f.read()
            self.file_map[self.file_path.absolute()] = rbuf
        return

class Master(Thread):
    '''
    Master线程是服务器的主线程，负责Worker线程的产生和控制

    Master线程实现用户列表的维护、用户登录情况记录、文件缓冲
    
    Worker线程是服务器处理客户端请求的线程，每一个客户端对应于一个Worker线程
    '''
    def __init__(self, bind_addr:tuple, user_list:list[UserInfo]) -> None:
        super().__init__(None, None, 'Master', daemon=False)

        self.running = True

        # worker_map 数据格式     ('ip', port):    [Worker, Queue,   UserInfo]
        # 使用 `worker.is_alive` 方法判断线程是否结束
        self.worker_map:dict[tuple[str, int], list[Worker, Queue, UserInfo|None]] = {}

        # user_map 数据格式 'user_id': [UserInfo, Worker,    is_login]
        self.user_map:  dict[str, list[UserInfo, Worker|None, bool]] = {}
        
        # file_cache 存储的数据格式 'file_path':bytes
        self.file_cache:dict[str, bytes] = {}
        self.file_cache.values()
        # 初始化 user_map
        self.__init_user_map(user_list)


        self.addr = bind_addr
        self.s = socket()
        self.s.bind(self.addr)
        self.s.listen(5)

        # accepted_socket 存储的数据格式 (socket, ('ip', port))
        self.accepted_socket = Queue()
        self.th_listen = Th_listen(self.s, self.accepted_socket)
        self.th_listen.start()
        
        return
    
    def run(self):
        '''
        对于新的连接，需要新建一个Worker线程进行处理

        对于Worker线程发来消息（即对应队列不为空），需要进行处理
        - 请求登录（防止多个账号同时登录）
        - 请求下载文件（非判断权限）利用缓存提高速度
        - 连接中断，请求资源清理
        '''
        while self.running:
            if not self.accepted_socket.empty():
                s, addr = self.accepted_socket.get()
                q = Queue()
                w = Worker(q, s)
                w.start()
                self.worker_map[addr] = [w, q, None, True]
            for addr,t in self.worker_map.items():
                w, q, info, is_alive = t
                # TODO 实现Master线程的run方法
                raise NotImplemented

    

    def stop(self):
        '''
        关闭Master线程

        该方法是安全的，当调用该方法时，
        
        将关闭监听端口，关闭所有Worker线程，关闭所有待处理的已连接的socket
        '''
        self.running = False
        self.s.close()
        for i in self.worker_map.values():
            w:Worker = i[1][0]
            w.stop()
        while not self.accepted_socket.empty():
            t:tuple[socket, tuple] = self.accepted_socket.get()
            t[0].close()
        return
    

    def __init_user_map(self, user_list:list[UserInfo]):
        '''
        内部方法，使用user_list构造user_map初始值
        '''
        for i in user_list:
            self.user_map[i.id] = [i, None, False]
        return
