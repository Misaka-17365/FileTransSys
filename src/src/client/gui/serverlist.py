""" 服务器列表模块

模块提供了服务器搜索的窗口和搜索方法

Classes:
    Th_search(Thread): 搜索线程
    ServerList(QWidget): 服务器列表显示窗口

    
注意，该窗口没有使用UI与功能单独实现的模式，UI与功能写在同一个类中
"""

from typing             import override, Callable

import time
from   threading import Thread, Event
import socket
import re

from PyQt5.QtCore       import Qt, pyqtSignal
from PyQt5.QtGui        import QCloseEvent, QShowEvent, QIcon
from PyQt5.QtWidgets    import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem



class Th_search(Thread):
    """搜索线程

    开启一个UDPsocket开始广播，并接收响应

    解析响应数据获得服务器的信息
    """

    @override
    def __init__(self, update_callback:Callable[[dict], None]) -> None:
        """重写初始化方法

        Args:
            update_callback (Callable[[dict], None]): 更新服务器列表的回调方法，当出现新的服务器时调用该方法
        """
        super().__init__(name='Searching-Server')                       # 调用父类初始化方法
        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)       # 创建一个UDP socket
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)    # 设置为允许广播
        self.s.settimeout(0.5)                                          # 设置超时
        self.update_callback = update_callback                          # 将回调挂在实例上
        self.endEvent = Event()                                         # 结束事件已便于停止线程
        return
    
    @override
    def run(self) -> None:
        """重写运行方法

        线程开启时将运行该方法
        """
        # 定义接收的合法格式
        rec_re = re.compile(r'RESPONSE_SERVER_<[a-zA-z0-9\-]*>_(?:(?:1[0-9][0-9]\.)|(?:2[0-4][0-9]\.)|(?:25[0-5]\.)|(?:[1-9][0-9]\.)|(?:[0-9]\.)){3}(?:(?:1[0-9][0-9])|(?:2[0-4][0-9])|(?:25[0-5])|(?:[1-9][0-9])|(?:[0-9]))_\d{1,5}')
        server_list = {}                    # 服务器列表 name:(name, ip, port)
        while not self.endEvent.is_set():
            self.s.sendto(f'REQUIRE_SERVER'.encode(), ('255.255.255.255', 57777))   # 广播请求
            recv_list = []
            while True:
                try:
                    recv_list.append(self.s.recvfrom(1024))     # 接收所有返回的数据
                except TimeoutError:
                    time.sleep(0.5)
                    break
            for buf,addr in recv_list:
                server_msg = buf.decode()                           # 解析返回的数据
                if not rec_re.match(server_msg):
                    continue
                server_msg = server_msg[server_msg.find('_<')+2:]
                t = server_msg.find('>_')
                name = server_msg[:t]
                addr = server_msg[t+2:].split('_')
                ip = addr[0]
                port = addr[1]
                server_list[name] = (name, ip, port)
            self.update_callback(server_list)               # 更新列表

    def shutdown(self) -> None:
        """关闭方法

        通知线程关闭
        """
        self.endEvent.set()


class ServerList(QWidget):
    """服务器列表界面类

    Signals:
        selected: 服务器被选中，携带(ip, port)
        doubleClicked: 服务器列表被双击
    """
    selected = pyqtSignal(tuple)
    doubleClicked = pyqtSignal()
    __list_update = pyqtSignal(dict)


    # ------------------------------ 初始化 -----------------------------

    @override
    def __init__(self) -> None:
        """重写初始化方法

        初始化UI，调用信号初始化方法
        """
        super().__init__()
        self.resize(800, 600)
        self.setWindowIcon(QIcon('resource/icon.svg'))
        
        self.setWindowTitle('服务器列表')
        layout = QVBoxLayout()

        fileList = QTableWidget()

        layout.addWidget(fileList)
        self.setLayout(layout)

        self.list = fileList
        self.list.setColumnCount(3)
        self.list.setHorizontalHeaderLabels(('名称', 'IP', '端口'))
        self.list.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignLeft)
        
        self.list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.list.setVerticalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        self.list.setHorizontalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)

        self.list.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.list.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.list.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.list.verticalHeader().setVisible(False)
        self.list.setColumnWidth(0, 300)
        self.list.setColumnWidth(1, 300)

        self.init_signals()
        return


    def init_signals(self) -> None:
        """初始化信号

        将信号与槽函数连接
        """
        self.__list_update.connect(self.on_list_update)
        self.list.cellClicked.connect(self.on_list_clicked)
        self.list.doubleClicked.connect(self.doubleClicked.emit)
        return
    


    # ------------------------------- 槽函数 -------------------------------------

    def on_list_update(self, d:dict) -> None:
        """列表更新槽函数

        根据触发信号时携带的参数更新服务器列表

        Args:
            d (dict): 包含服务器信息的字典
        """
        l = len(d)
        self.list.setRowCount(l)                    # 根据服务器个数初始化表格控件
        for i,row in zip(d.values(), range(l)):     # 依次将服务器信息填入表格
            self.list.setItem(row, 0, QTableWidgetItem(i[0]))
            self.list.setItem(row, 1, QTableWidgetItem(i[1]))
            self.list.setItem(row, 2, QTableWidgetItem(i[2]))

    
    def on_list_clicked(self, row:int, col:int) -> None:
        """服务器选中槽函数

        当点击服务器列表的任意项时，该槽函数执行

        Args:
            row (int): 点击的行坐标
            col (int): 点击的列坐标

        由于服务器列表以行为单位，因此列坐标没有使用
        """
        ip = self.list.item(row, 1).text()      # 获取对应行的ip    
        port = self.list.item(row, 2).text()    # 获取对应行的port
        self.selected.emit((ip, port))          # 发射选中信号
        return

    def start_search(self) -> None:
        """开始搜索服务器

        启动搜索线程，将 __list_update.emit 作为更新的回调传入

        如果已经有一个搜索线程且正在运行，则函数直接返回
        """
        if hasattr(self, 'th_search') and self.th_search.is_alive():
            return
        self.th_search = Th_search(self.__list_update.emit)
        self.th_search.start()
        return

    def stop_search(self) -> None:
        """停止搜索服务器

        通知搜索线程停止

        如果没有停止线程，则不执行任何操作
        """
        if hasattr(self, 'th_search') and self.th_search.is_alive():
            self.th_search.shutdown()
        return
    

    #---------------------------------------------------------------#
    # 以下两个方法为重写的PyQt事件处理器                               #
    # 当窗口出现特定行为时，以下方法被自动调用                          #
    # 重写没有影响原本的功能                                          #
    # 重写后增加了一个功能：在窗口打开时搜索服务器，关闭时自动停止搜索    #
    #---------------------------------------------------------------#
    @override
    def showEvent(self, a0: QShowEvent | None) -> None:
        self.start_search()
        return super().showEvent(a0)
    @override
    def closeEvent(self, a0: QCloseEvent | None) -> None:
        self.stop_search()
        return super().closeEvent(a0)
