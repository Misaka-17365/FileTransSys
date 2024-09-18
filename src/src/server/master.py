""" 管理者模块

实现了管理者线程类和监听线程类

Classes:
    Th_listen(Thread): 监听线程类
    Master(Thread): 管理者线程类

"""


from typing import override, Dict, List, Tuple

import time
import logging
from socket import socket
from queue import Queue
from threading import Thread, Event

from ..globals import StatCode
from .userinfo import UserInfo
from .worker import Worker
from .serverconfig import ServerConfig



class Th_listen(Thread):
    '''
    该线程仅进行监听,不进行监听之外的任何操作

    需要关闭该线程时,直接将监听的socket关闭,线程自动退出

    线程在退出前会向队列里写入一个空元组 (None, None)
    '''
    @override
    def __init__(self, socket:socket, queue:Queue):
        super().__init__(None, None, 'Th_listen', daemon=False)
        self.name = 'Master Listening'
        self.s = socket
        self.q = queue
        return
    @override
    def run(self):
        '''
        阻塞监听，将监听到的连接添加到队列中，送入 Master 线程

        当监听的socket出现意外时,不再进行监听,向队列写入空元组，线程自动退出
        '''
        while True:
            acp = self.s.accept()
            self.q.put(acp)
    @override
    def excepthook(self, e):
        self.q.put((None, str(e)))
        return



    

class Master(Thread):
    '''
    Master线程是服务器的主线程，负责Worker线程的产生和控制

    Master线程实现用户列表的维护、用户登录情况记录
    
    Worker线程是服务器处理客户端请求的线程，每一个客户端对应于一个Worker线程
    '''
    @override
    def __init__(self, bind_addr:Tuple[str, int], user_list:list[UserInfo]) -> None:
        super().__init__(None, None, 'Master', daemon=False)
        ServerConfig.log.info(f'{"服务器初始化":^30}'.replace(' ', '-'))
        self.running = True

        # worker_map 数据格式     ('ip', port):Worker
        self.worker_map:Dict[tuple[str, int], Worker] = {}

        # user_map 数据格式 'user_id': [UserInfo, Worker]
        self.user_map:  Dict[str, tuple[UserInfo, Worker]] = {}
    
        # 初始化 user_map
        ServerConfig.log.info('初始化用户列表')
        self.__init_user_map(user_list)

        # 开始监听
        ServerConfig.log.info(f'开始监听{bind_addr}')
        self.addr = bind_addr
        self.s = socket()
        self.s.bind(self.addr)
        self.s.listen(10)
        # accepted_socket 存储的数据格式 (socket, ('ip', port))
        self.accepted_socket = Queue()
        self.th_listen = Th_listen(self.s, self.accepted_socket)
        self.th_listen.start()
        
        self.msgBufs = Queue()
        self.msgBufr = Queue()
        ServerConfig.log.info(f'{"服务器初始化结束":^30}'.replace(' ', '-'))
        return
    
    @override
    def run(self) -> None:
        '''
        对于新的连接，需要新建一个Worker线程进行处理

        对于Worker线程发来消息（即对应队列不为空），需要进行处理
        - 消息分发
        - 请求登录（防止多个账号同时登录）
        - 连接中断，请求资源清理
        '''
        while self.running:
            msg_list = []
            # 初始化服务器端消息
            while not self.msgBufs.empty():
                msg_list.append(self.msgBufs.get())
            # 处理新连接
            if not self.accepted_socket.empty():
                s, addr = self.accepted_socket.get()
                w = Worker(s)
                w.start()
                self.worker_map[addr] = w
                ServerConfig.log.info(f'{addr} 已连接到服务器')
            # 处理Worker的请求
            for addr,worker in self.worker_map.items():
                while not worker.queue.empty():
                    cmd, args, event, retval = worker.queue.get()
                    cmd:str
                    args:list
                    event:Event
                    retval:list
                    if cmd == 'user':
                        if not args[0] in self.user_map.keys():
                            retval.extend([StatCode.ERR_USER_UNDEFINED, None])
                            event.set()
                            ServerConfig.log.warning(f'{worker.socket.getpeername()} 尝试登录到{args[0]}，已拒绝[无效用户名]')
                            continue
                        user_info, w = self.user_map[args[0]]
                        if user_info.passwd != args[1]:
                            retval.extend([StatCode.ERR_PSWD_UNMATCH, None])
                            event.set()
                            ServerConfig.log.warning(f'{worker.socket.getpeername()} 尝试登录到{args[0]}，已拒绝[密码错误]')
                            continue
                        ServerConfig.log.info(f'{worker.socket.getpeername()} 已登录至 {args[0]}')
                        if w is not None and w.logined == True:
                            ServerConfig.log.info(f'{w.socket.getpeername()} 已下线，由于{worker.socket.getpeername()}使用该用户{args[0]}登录')
                            w.stop()
                            continue
                        self.user_map[args[0]][1] = worker
                        retval.extend([StatCode.SUCCESS, user_info])
                        event.set()
                        continue
                    elif cmd == 'msg':
                        msg_list.append(args[0])
                        retval.extend([StatCode.SUCCESS, None])
                        event.set()
                        continue
                    else:
                        retval.extend([StatCode.ERR_NO_PERMISSION, None])
                        event.set()
                        continue
            # 给已登录的Worker分发消息，清理已停止的线程
            dead_workers = []
            for key, pare in self.user_map.items():
                worker = pare[1]
                if worker is None:
                    continue
                if not worker.running or not worker.is_alive():
                    dead_workers.append(key)
                    continue
                for i in msg_list:
                    if ServerConfig.PERMISSION['distributeMessage'] or i[0] == worker.userinfo.id or i[0] == 'SERVER':
                        worker.msgbuf.put(i)
            self.worker_map = dict(filter(lambda k: k[1].is_alive(), list(self.worker_map.items())))
            for i in dead_workers:
                self.user_map[i][1] = None
            for i in msg_list:
                self.msgBufr.put(i)
            # 继续下一循环
            time.sleep(0.01)
            continue


    def sendMsg(self, s:str) -> None:
        """发送消息方法

        供服务端端本地发送消息的方法，可以实现服务端直接向客户端发送消息

        Args:
            s (str): 消息内容
        """
        self.msgBufs.put(('SERVER', time.localtime(), s))
        return


    def stop(self) -> None:
        '''
        关闭Master线程

        该方法是安全的，当调用该方法时，
        
        将关闭监听端口，关闭所有Worker线程，关闭所有待处理的已连接的socket
        '''
        self.running = False
        self.s.close()
        for i in self.worker_map.values():
            i.stop()
        while not self.accepted_socket.empty():
            t:tuple[socket, tuple] = self.accepted_socket.get()
            if t[0]:
                t[0].close()
        return
    

    def __init_user_map(self, user_list:List[UserInfo]) -> None:
        '''
        内部方法，使用user_list构造user_map初始值
        '''
        for i in user_list:
            self.user_map[i.id] = [i, None]
        return
