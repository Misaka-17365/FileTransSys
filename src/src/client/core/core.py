""" src.client.core.core

客户端核心逻辑模块

Classes:
    Th_send(Thread): 管理socket发送的线程
    Th_receive(Thread): 管理socket接收的线程
    Client(object): 客户端核心逻辑类，提供API供调用


"""

from typing import override
from threading import Thread, Event, Lock
from queue import Queue, Empty
import socket

from ...globals import Package
from .errcode import ErrCode


class Th_send(Thread):
    """Th_send 发送线程

    负责将队列中的数据包取出并编码发送
    """
    @override
    def __init__(self, s:socket.socket, endEvent:Event, abortEvent:Event) -> None:
        """重写线程的初始化函数

        Args:
            s (socket.socket): 控制的socket
            endEvent (Event): 结束事件，用于控制线程退出
            abortEvent (Event): 中断事件，向Client类通知连接断开
        
        """
        super().__init__(None, None, 'Th_send', None, None) # 调用父类初始化方法
        self.buf = Queue()          # 新建数据包队列，线程发送的数据包从这里取
        self.s = s                  # 绑定socket
        self.daemon = True          # 设置为“守护线程”，其他线程退出后自动退出
        self.endEvent = endEvent    # 结束事件，用于外部控制线程关闭
        self.abortEvent = abortEvent    # 中断事件，通知外部连接断开

    @override
    def run(self) -> None:
        """重写运行方法

        这里是线程运行的主要代码

        从队列中取出数据包，然后将数据包编码发送
        """
        while not self.endEvent.is_set():   # 判断外部是否发出停止信号
            try:
                # 这里使用超时是为了配合停止信号
                # 如果不设置超时，运行会一直卡在这里，就不会回到循环的开头，进行条件验证
                # 外部无法控制线程结束
                pkg:Package = self.buf.get(timeout=0.5)
            except Empty:
                continue
            pkg_b = pkg.to_bytes()          # 对得到的数据包编码
            try:
                self.s.sendall(pkg_b)       # 发送二进制数据
            except:
                self.abortEvent.set()

class Th_receive(Thread):
    """Th_receive 接收线程

    负责接收二进制数据，还原成数据包放到接收表中

    接收表为了满足线程安全，采用 **注册/注销** 模式，即：  
        - 如果需要添加接收表项，则需要注册一个接收信息  
        - 如果需要删除，则需要注销  
        - 不可以直接操作接收表
    
    类提供了注册/注销的API，线程安全，可以多线程直接调用
    """

    @override
    def __init__(self, s:socket.socket, endEvent:Event) -> None:
        """重写初始化函数

        Args:
            s (socket.socket): 控制的socket
            endEvent (Event): 结束事件，用来实现外部控制线程停止
        """
        super().__init__(None, None, 'Th_receive', None, None)  # 调用父类初始化方法
        self.buf:dict[int, Package] = {}        # 建立接收表
        self.s = s                              # 将socket挂在实例上
        self.daemon = True                      # 设定为守护线程
        self.buf_lock = Lock()                  # 用于实现线程安全的锁
        self.endEvent = endEvent                # 将结束事件挂在实例上

    @override
    def run(self) -> None:
        """重写运行方法

        从socket接收数据包，放在接收表中
        """
        while not self.endEvent.is_set():
            try:
                pkg_length = int.from_bytes(self.read_s_by_int(4))  # 获取4字节长度的整型数据
            except:
                self.endEvent.set()
                continue
            pkg_b = self.read_s_by_int(pkg_length)      # 获取整个数据包的二进制数据
            pkg = Package.from_bytes(pkg_b)             # 解析成数据包
            with self.buf_lock:
                # 如果已经有相应的注册id，则放入对应位置触发接收事件
                # 如果没有注册，则数据包被丢弃
                if pkg.id in self.buf.keys():           
                    self.buf[pkg.id][1].append(pkg)
                    self.buf[pkg.id][0].set()

                

    
    def regist(self, id:int, event:Event, retval:list) -> None:
        """注册接收表方法

        Args:
            id (int): 数据包id
            event (Event): 接收事件
            retval (list): 返回值的容器

        将传入的id作为接收表的key
        
        当接收到对于id的数据包时，数据包将被放入容器retval并触发接收事件
        """
        with self.buf_lock:
            self.buf[id] = (event, retval)
            
    
    def deregist(self, id:int) -> None:
        """注销接收表方法

        Args:
            id (int): 数据包id

        将对应id的接收表项删除
        """
        with self.buf_lock:
            del self.buf[id]
    
    def read_s_by_int(self, i:int) -> bytearray:
        """从socket获取固定字节的数据

        Args:
            i (int): 数据长度（字节数）

        Returns:
            bytearray: 所需的数据

        这个函数封装了socket.recv函数，实现了读取固定长度

        原版socket.recv函数无法确定读取的长度，只能限制最大长度
        """
        buf = bytearray(i)      # 根据数据长度实例化一个字节数组
        readed = 0              # 已接收的字节数量
        while readed < i:
            r = self.s.recv(i - readed)
            buf[readed:readed+len(r)] = r   # 将获取到的bytes合并到buf中
            readed += len(r)                # 更新已接收的长度
        return buf



class ClientCore:
    '''
    客户端核心类

    将所有抽象接口实现，完成客户端的必要的功能，
    包括连接服务端、登录、获取文件列表、
    发送消息、接收消息、发送文件、接收文件、
    获取/设定服务端的选项等功能
    '''
    @override
    def __init__(self) -> None:
        """重写初始化函数

        由于没有建立连接，所有属性均为空
        """
        self.s = None
        self.is_connected = False
        self.th_send = None
        self.th_receive = None
    
    def connect(self, addr:tuple) -> bool:
        """连接方法

        Args:
            addr (tuple): 连接的地址

        Returns:
            bool: 连接是否成功
        """
        self.s = socket.socket()        # 新建一个socket用于连接
        self.s.settimeout(3)
        err = self.s.connect_ex(addr)   # 连接服务器
        self.s.settimeout(None)
        if err:                         # 超时返回False
            self.s = None            
            return False
        self.is_connected = True        # 更改状态
        self.init_connected()           # 执行连接后初始化
        return True
    
    def init_connected(self) -> None:
        """连接后初始化

        建立结束事件、中断事件、发送线程和接收线程

        开始监控连接状况
        """
        self.endEvent = Event()
        self.abortEvent = Event()
        self.th_send = Th_send(self.s, self.endEvent, self.abortEvent)
        self.th_receive = Th_receive(self.s, self.endEvent)
        self.th_send.start()
        self.th_receive.start()
        self.start_connection_moniter()

    def start_connection_moniter(self) -> None:
        """启动连接监控
        
        开启一个线程监控连接情况，当连接断开时，自动将is_connected属性设置为False
        """
        def moniter():
            self.abortEvent.wait()
            self.is_connected = False
            return
        Thread(target=moniter, name='connection moniter', daemon=True).start()


    def require(self, cmd:str, args:list, timeout:float = 2) -> tuple:
        """请求的原始方法

        所有API均为该方法的包装

        Args:
            cmd (str): API的命令
            args (list): 命令对应的参数
            timeout (float, optional): 超时时间. Defaults to 2.

        Returns:
            tuple: 返回请求的结果，即返回包的args
        """
        if not self.is_connected:                   # 判断连接状态，未连接则直接返回错误
            return (ErrCode.ERR_NO_LOGIN, None)
        pkg = Package(Package.get_id(), cmd, args)  # 构造请求数据包
        finish = Event()                            # 新建完成事件（接收事件）
        retval = []                                 # 返回值容器
        self.th_receive.regist(pkg.id, finish, retval)  # 注册接收表
        self.th_send.buf.put(pkg)                   # 发送数据包
        ok = finish.wait(timeout)                   # 等待接收
        if ok:
            # 接收成功后将数据包取出，将数据包中的args返回
            # 无论是否超时，均需要对接收表进行注销
            pkg:Package = retval[0]                 
            self.th_receive.deregist(pkg.id)
            return tuple(pkg.args)
        else:
            # 超时返回错误                                      
            self.th_receive.deregist(pkg.id)
            return (ErrCode.ERR_TIME_OUT, None)
    
    def close(self) -> None:
        """核心关闭方法

        通知子线程停止运行，关闭socket
        """
        if hasattr(self, 'endEvent'):
            self.endEvent.set()
        self.s.close()

    # --------------------------------------------------------------#
    # 以下 6 个方法为暴露的 API                                       #
    # 这些方法均为 require 方法的包装                                 #
    # 对于文件传输，会将返回的端口号进行连接，返回的是已连接的 socket    #
    # --------------------------------------------------------------#
    
    def login(self, user_id:str, user_pswd:str) -> tuple[ErrCode, None]:
        return self.require('login', [user_id, user_pswd])
        
    def getFileList(self, dir_path:str) -> tuple[ErrCode, tuple[list[str], list[tuple]]]:
        return self.require('getFileList', [dir_path])
    
    def getMessage(self) -> tuple[ErrCode, list[tuple[str, tuple, str]]]:
        return self.require('getMessage', [])
    
    def putMessage(self, msg:str) -> tuple[ErrCode, None]:
        return self.require('putMessage', [msg])
    
    def getFile(self, file_path:str, begin_byte:int) -> tuple[ErrCode, tuple[int, int]]:
        err, addon = self.require('getFile', [file_path, begin_byte])
        if err:
            return(err, addon)
        port = addon[0]
        s = socket.socket()
        s.connect((self.s.getpeername()[0], port))
        return (err, (s, addon[1]))
    
    def putFile(self, file_path:str, file_size:int) -> tuple[ErrCode, tuple[int]]:
        err, addon =  self.require('putFile', [file_path, file_size])
        if err:
            return(err, addon)
        port = addon[0]
        s = socket.socket()
        s.connect((self.s.getpeername()[0], port))
        return (err, (s,))
        

