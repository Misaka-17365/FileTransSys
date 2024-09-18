""" 工作者线程模块

实现了工作者线程及必须的发送线程、接收线程和文件传输线程

Classes:
    Recver(Thread): 接收线程
    Sender(Thread): 发送线程
    Worker(Thread): 工作者线程

"""

from typing import Any, List, override, Literal

import os
from pathlib import Path
import time
from socket import socket
from queue import Queue
from threading import Thread, Event

from ..globals import Package, StatCode
from .userinfo import UserInfo
from .serverconfig import ServerConfig


def readSocketSize(s:socket, size:int) -> bytes:
    """从socket读取固定字节数的函数

    Args:
        s (socket): 要读取的socket
        size (int): 读取的数量

    Returns:
        bytes: 结果
    """
    readed = 0
    retval = bytearray(size)
    mv = memoryview(retval)
    while readed < size:
        rbuf = s.recv(min(4096, size - readed))
        rlen = len(rbuf)
        mv[readed:readed+rlen] = rbuf
        readed += rlen
    return bytes(retval)


class Recver(Thread):
    """
    接收客户端请求的线程
    """
    @override
    def __init__(self, queue:Queue, socket:socket) -> None:
        super().__init__(None, None, f'Worker-{socket.getpeername()[0]}-Recver')
        self.queue = queue
        self.s = socket
        self.running = True
        return
    
    @override
    def run(self) -> None:
        while self.running:
            try:
                plen = int.from_bytes(readSocketSize(self.s, 4), 'big') # 读取头部4字节，确定包大小
                pkg_b = readSocketSize(self.s, plen)        # 读取完整数据包
                pkg = Package.from_bytes(pkg_b)             # 解析数据包
                self.queue.put(pkg)                         # 将数据包放入队列
            except:
                # 当发生异常时，线程退出，并向队列里放入一个 None
                self.queue.put(None)
                return
        
    def stop(self) -> None:
        """通知线程通知运行

        将运行状态改为停止，并将socket超时设定为0，立即超时返回
        """
        self.running = False
        self.s.settimeout(0)
        return
    
class Sender(Thread):
    """
    向客户端发送响应的线程
    """
    @override
    def __init__(self, queue:Queue, socket:socket) -> None:
        super().__init__(None, None, f'Worker-{socket.getpeername()[0]}-Sender')
        self.queue = queue
        self.s = socket
        self.running = True
        return
    
    @override
    def run(self):
        while self.running:
            pkg:Package = self.queue.get()
            if pkg:
                self.s.sendall(pkg.to_bytes())
    
    def stop(self):
        """通知线程通知运行

        将运行状态改为停止，并向队列投入一个None，打破阻塞状态
        """
        self.running = False
        self.queue.put(None)
        return


class Th_fileTrans(Thread):
    """文件传输线程

    该线程控制文件上传与下载，下载完成后自动写入硬盘
    """

    @override
    def __init__(
        self, 
        type:Literal['s', 'r'], 
        socket:socket, 
        file_path:Path, 
        file_size:int,
        file_start_point:int,
        peer_ip:str
        ) -> None:
        """重写初始化方法

        Args:
            type (Literal[&#39;s&#39;, &#39;r&#39;]): 线程的类型：发生/接收
            socket (socket): 正在监听等待连接的socket
            file_path (Path): 本地文件路径
            file_size (int): 文件大小
            file_start_point (int): 文件起始点
            peer_ip (str): 待传输客户端的IP地址
        """
        super().__init__(None, None, None, None)
        self.type = type
        self.s = socket
        self.file_path = file_path
        self.file_size = file_size
        self.start_point = file_start_point
        self.peer_ip = peer_ip
        return
    
    @override
    def run(self):
        self.s.listen(5)
        self.s.settimeout(3)
        while True:
            try:
                c, addr = self.s.accept()
            except TimeoutError:
                ServerConfig.log.info(f'文件传输等待超时. 文件[{self.file_path}]. 等待对方IP[{self.peer_ip}]')
                self.s.close()
                return
            if addr[0] != self.peer_ip:
                c.close()
            else:
                break

        # 发送文件
        # 1. 从硬盘读取文件
        # 2. 构建 memoryview 提升性能
        # 3. 发送全部数据
        # 4. 关闭socket
        if self.type == 's':
            with open(self.file_path, 'rb') as f:
                buf = f.read()
            cursor = self.start_point
            mv = memoryview(buf)
            c.sendall(mv[cursor:])
            c.recv(1)
            ServerConfig.log.info(f'{c.getpeername()} 已下载文件 [{self.file_path}]')
            c.close()
            return
        # 接收文件
        # 1. 开辟一片内存缓冲区
        # 2. 构建 memoryview 提升性能
        # 3. 开始接收
        # 4. 接收完成后关闭socket，将数据写入硬盘
        else:
            buf = bytearray(self.file_size)
            mv = memoryview(buf)
            cursor = 0
            size = self.file_size
            while cursor < size:
                rbuf = c.recv(min(8192, size - cursor))
                rl = len(rbuf)
                buf[cursor:cursor+rl] = rbuf
                cursor += rl
            c.close()
            with open(self.file_path, 'wb') as f:
                f.write(buf)
            ServerConfig.log.info(f'{c.getpeername()} 已上传文件 [{self.file_path}]')
            return


class Worker(Thread):
    '''
    处理客户端请求的线程

    客户端连接到服务器时，监听socket返回一个已经建立连接的 `socket` ，

    使用该`socket`实例化Worker线程，即这个Worker线程负责处理这个`socket`后面的客户端的请求
    '''
    @override
    def __init__(self, socket:socket) -> None:
        """重写初始化方法

        Args:
            socket (socket): 新连接的socket
        """
        super().__init__(None, None, f'Worker-{socket.getpeername()[0]}')
        self.queue = Queue()        # 请求队列
        self.msgbuf = Queue()       # 消息队列
        self.socket = socket        
        self.running = True

        self.userinfo:UserInfo = None   # 对应客户端登录用户的信息，登陆后才有效
        self.logined = False

        # 发送和接收线程相关
        self.rbuf = Queue()
        self.recver = Recver(self.rbuf, socket)
        self.sbuf = Queue()
        self.sender = Sender(self.sbuf, socket)
        self.recver.start()
        self.sender.start()
        return
    
    @override
    def run(self) -> None:
        while self.running:
            pkg = self.getPkg()
        
            if pkg is None:         # 断开连接时接收线程会向队列中放入一个None
                self.logined = False
                ServerConfig.log.info(f'{self.socket.getpeername()} 已断开连接')
                self.stop()
                break

            if not self.logined:    # 进行登录检验
                if pkg.cmd != 'login':
                    self.ret(pkg, StatCode.ERR_NO_LOGIN)
                    ServerConfig.log.warning(f'{self.socket.getpeername()} 尝试访问资源，已拒绝[未登录]')
                    continue
                # 请求登录的处理
                user_id = pkg.args[0]
                passwd = pkg.args[1]
                (code, userinfo) = self.__askMaster('user', [user_id, passwd])
                if code == StatCode.SUCCESS:
                    self.userinfo = userinfo
                    self.logined = True
                self.ret(pkg, code)
                continue
            
            # 具体业务处理
            cmd = pkg.cmd
            if cmd == 'getFileList':
                if not ServerConfig.PERMISSION['allUserGetFilelist']:
                    self.ret(pkg, StatCode.ERR_NO_PERMISSION)
                    ServerConfig.log.info(f'{self.socket.getpeername()} 尝试访问文件列表，已拒绝[无全局权限]')
                    continue
                dir_path = Path('.'+pkg.args[0])
                root_path = ServerConfig.SHARE_DIR
                path = root_path.joinpath(dir_path)
                if path.is_dir():
                    l = os.listdir(path)
                    file_list = []
                    dir_list = []
                    for i in l:
                        if path.joinpath(i).is_dir():
                            dir_list.append(i)
                        else:
                            filePath = path.joinpath(i)
                            filestat = filePath.stat()
                            file_list.append((i, filePath.suffix, filestat.st_size, filestat.st_mtime))
                    self.ret(pkg, StatCode.SUCCESS, [dir_list, file_list])
                    continue
                self.ret(pkg, StatCode.ERR_DIR_NOT_EXIST, None)
                continue

            elif cmd == 'getMessage':
                if not ServerConfig.PERMISSION['allUserGetMessage']:
                    self.ret(pkg, StatCode.ERR_NO_PERMISSION)
                    ServerConfig.log.info(f'{self.socket.getpeername()} 尝试获取消息，已拒绝[无全局权限]')
                    continue
                if not self.userinfo.per_msg_d:
                    self.ret(pkg, StatCode.ERR_NO_PERMISSION)
                    ServerConfig.log.warning(f'{self.socket.getpeername()} 尝试获取消息，已拒绝[无用户权限]')
                    while not self.msgbuf.empty():
                        self.msgbuf.get()
                    continue
                msg_list = []
                while not self.msgbuf.empty():
                    msg_list.append(self.msgbuf.get())
                self.ret(pkg, StatCode.SUCCESS, msg_list)
                continue

            elif cmd == 'putMessage':
                if not ServerConfig.PERMISSION['allUserPutMessage']:
                    self.ret(pkg, StatCode.ERR_NO_PERMISSION)
                    ServerConfig.log.info(f'{self.socket.getpeername()} 尝试推送消息，已拒绝[无全局权限]')
                    continue
                if not self.userinfo.per_msg_u:
                    self.ret(pkg, StatCode.ERR_NO_PERMISSION)
                    ServerConfig.log.warning(f'{self.socket.getpeername()} 尝试推送消息，已拒绝[无用户权限]')
                    continue
                msg = (self.userinfo.id, time.localtime(), pkg.args[0])
                code = self.__askMaster('msg', [msg])
                self.ret(pkg, code[0], None)
                continue

            elif cmd == 'getFile':
                if not ServerConfig.PERMISSION['allUserDownloadFile']:
                    self.ret(pkg, StatCode.ERR_NO_PERMISSION)
                    ServerConfig.log.info(f'{self.socket.getpeername()} 尝试下载文件，已拒绝[无全局权限]')
                    continue
                if not self.userinfo.per_file_d:
                    self.ret(pkg, StatCode.ERR_NO_PERMISSION)
                    ServerConfig.log.warning(f'{self.socket.getpeername()} 尝试下载文件，已拒绝[无用户权限]')
                    continue
                rfp = pkg.args[0][1:]
                bp = pkg.args[1]
                afp = ServerConfig.SHARE_DIR.joinpath(rfp)
                if not afp.exists() or afp.is_dir():
                    self.ret(pkg, StatCode.ERR_FILE_NOT_EXIST)
                    ServerConfig.log.info(f'{self.socket.getpeername()} 尝试下载文件，失败[无目标文件]')
                    continue
                s = self.__get_sock()
                port = s.getsockname()[1]
                size = afp.stat().st_size
                ServerConfig.log.info(f'{self.socket.getpeername()} 下载文件[{afp}]，大小[{size}]字节, 端口[{port}]')
                self.ret(pkg, StatCode.SUCCESS, [port, size])
                Th_fileTrans('s', s, afp, size, bp, self.socket.getpeername()[0]).start()
                continue

            elif cmd == 'putFile':
                if not ServerConfig.PERMISSION['allUserUploadFile']:
                    self.ret(pkg, StatCode.ERR_NO_PERMISSION)
                    ServerConfig.log.info(f'{self.socket.getpeername()} 尝试上传文件，已拒绝[无全局权限]')
                    continue
                if not self.userinfo.per_file_u:
                    self.ret(pkg, StatCode.ERR_NO_PERMISSION)
                    ServerConfig.log.warning(f'{self.socket.getpeername()} 尝试上传文件，已拒绝[无用户权限]')
                    continue
                rfp = '.'+pkg.args[0]
                afp = ServerConfig.SHARE_DIR.joinpath(rfp)
                if afp.exists() :
                    self.ret(pkg, StatCode.ERR_FIEL_ALREADY_EXIST)
                    ServerConfig.log.info(f'{self.socket.getpeername()} 尝试上传文件，失败[目标文件已存在]')
                    continue
                size = pkg.args[1]
                s = self.__get_sock()
                port = s.getsockname()[1]
                ServerConfig.log.info(f'{self.socket.getpeername()} 上传文件[{afp}]，大小[{size}]字节, 端口[{port}]')
                Th_fileTrans('r', s, afp, size, 0, self.socket.getpeername()[0]).start()
                self.ret(pkg, StatCode.SUCCESS, [port])
                continue
                
            else:
                continue


    def stop(self) -> None:
        """停止该工作者线程

        停止该工作者线程，停止发送和接收线程，关闭socket
        """
        ServerConfig.log.info(f'{self.socket.getpeername()} 由服务器端主动断开')
        self.running = False
        self.recver.stop()
        self.sender.stop()
        self.socket.close()
        return

    # 包装方法，以简化逻辑
    def getPkg(self) -> Package:
        return self.rbuf.get()
    def putPkg(self, pkg:Package):
        self.sbuf.put(pkg)
        return
    

    def __askMaster(self, cmd:str, args:List) -> Any:
        """工作者线程向管理者线程询问的方法

        将复杂的异步请求包装成一个阻塞的函数调用

        Args:
            cmd (str): 询问类型
            args (List): 参数

        Returns:
            Any: 可能的任何值
        """

        event = Event()     # 新建一个完成事件
        retval = []         # 新建返回值容器
        self.queue.put((cmd, args, event, retval))  # 将必要的内容放入队列
        event.wait()        # 等待管理者线程回答
        return retval       # 返回需要的返回值
    
    def __get_sock(self) -> socket:
        """获取一个可用的socket

        工具方法

        Returns:
            socket: 已绑定到空闲端口的socket
        """
        s = socket()
        s.bind(('0.0.0.0', 0))
        return s
    
    def ret(self, pkg:Package, code:StatCode, addon:Any = None):
        """向客户端返回数据包

        将数据包的构建放入该函数以简化响应逻辑

        Args:
            pkg (Package): 客户端发送来的数据包
            code (StatCode): 本次操作的状态码
            addon (Any, optional): 附加数据. Defaults to None.
        """
        id = pkg.id
        cmd = 'return'
        args = [code, addon]
        new_pkg = Package(id, cmd, args)
        self.putPkg(new_pkg)
        return
