""" 服务器地址广播模块

提供了一个可以广播服务器地址的线程类

Classes:
    Th_broadcast(Thread): 广播线程

"""


from typing import override

import time
import socket

from threading import Thread


class Th_broadcast(Thread):
    """服务器地址广播线程

    启动后根据参数自动广播服务器的地址

    线程会在特定的UDP端口监听消息，当接收到来自客户端的请求时，向该客户端发送当前服务器的信息
    """
    @override
    def __init__(self, name:str, ip:str, port:int) -> None:
        super().__init__(name='broadcast', daemon=True)
        self.server_name = name
        self.ip = ip
        self.port = port
        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.s.bind(('0.0.0.0', 57777))         # 固定在端口57777进行广播

    @override
    def run(self):
        while True:
            time.sleep(0.2)
            # 接收地址请求
            buf, addr = self.s.recvfrom(1024)
            if buf.decode() != 'REQUIRE_SERVER':
                continue
            # 向请求地址发送服务器的信息
            self.s.sendto(f'RESPONSE_SERVER_<{self.server_name}>_{self.ip}_{self.port}'.encode(), addr)



# coding时保留的入口，用于调试
# 运行当前文件可以开启地址广播
if __name__ == '__main__':
    t = Th_broadcast('dummy_server', '127.0.0.1', 2222)
    t.start()
    time.sleep(1000)