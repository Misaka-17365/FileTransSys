""" 文件对话界面模块

Classes:
    Th_dl(QThread): 下载线程
    Th_ul(Qthread): 上传线程
    Filedialog(src.client.gui.gui_filedialog.GUI_Filedialog): 文件对话界面类

"""

from   typing           import override, Literal
import socket
from   threading        import Event

from   PyQt5.QtCore     import pyqtSignal, QThread
from   PyQt5.QtGui      import QCloseEvent, QShowEvent

from   .gui_filedialog  import GUI_Filedialog



class Th_dl(QThread):
    """文件下载线程

    完成文件接收的工作，并将接收到的数据以信号参数的形式传递出
    
    继承于QThread

    Signals:
        prograss_update: 通知进度条更新进度，携带(recved_size)
        finished: 通知完成接收

    """
    progress_update = pyqtSignal(int)
    finished = pyqtSignal(bytearray)

    @override
    def __init__(self, s:socket.socket, file_size:int, endEvent:Event) -> None:
        """重写初始化方法

        Args:
            s (socket.socket): 用来传输文件数据的socket
            file_size (int): 文件大小
            endEvent (Event): 停止事件
        """
        super().__init__()
        self.end = endEvent
        self.s = s
        self.file_size = file_size

    @override
    def run(self) -> None:
        """重写运行方法

        接收数据，写入缓冲，梅接收一次数据发射一次 prograss_updated 信号
        
        接收完成后发射 finished 信号，将接收的数据传出
        """
        dled_size = 0
        buf = bytearray(self.file_size)
        while not self.end.is_set():
            r = self.s.recv(min(8192, self.file_size - dled_size))
            l = len(r)
            buf[dled_size:dled_size+l] = r
            dled_size += l
            self.progress_update.emit(dled_size)
            if dled_size == self.file_size:
                if dled_size == 0:
                    self.progress_update.emit(1)
                self.finished.emit(buf)
                self.s.close()
                break
        else:
            self.s.close()


class Th_ul(QThread):
    """文件上传线程

    完成文件发送的工作
    
    继承于QThread

    Signals:
        prograss_update: 通知进度条更新进度，携带(recved_size)
        finished: 通知完成接收

    """

    progress_update = pyqtSignal(int)
    finished = pyqtSignal()

    @override
    def __init__(self, s:socket.socket, buffer:bytes, endEvent:Event) -> None:
        """重写初始化方法

        Args:
            s (socket.socket): 用来传输文件数据的socket
            buffer (bytes): 文件数据
            endEvent (Event): 停止事件
        """
        super().__init__()
        self.end = endEvent
        self.s = s
        self.buffer = buffer
        return
    
    @override
    def run(self) -> None:
        """重写运行方法

        将数据分段发送，每发送一次发射一次 prograss_updated 信号
        
        接收完成后发射 finished 信号
        """
        uled_size = 0
        file_size = len(self.buffer)
        mv = memoryview(self.buffer)        # 使用 memoryview 直接访问内存，减小创建对象的开销
        while not self.end.is_set():
            l = self.s.send(mv[uled_size:uled_size+min(8192, file_size - uled_size)])
            uled_size += l
            self.progress_update.emit(uled_size)
            if uled_size == file_size:
                if uled_size == 0:
                    self.progress_update.emit(1)
                self.finished.emit()
                self.s.close()
                break
        else:
            self.s.close()
        return



class Filedialog(GUI_Filedialog):
    """文件对话界面类

    实现文件对话界面的全部功能
    """

    @override
    def __init__(self, 
                 file_name:str, 
                 opt:Literal['upload', 'download'], 
                 file_size:int, 
                 socket:socket.socket,
                 dpath:str) -> None:
        """重写初始化方法

        Args:
            file_name (str): 文件名
            opt (Literal[&#39;upload&#39;, &#39;download&#39;]): 上传/下载选项
            file_size (int): 文件大小
            socket (socket.socket): 用于传输的socket
            dpath (str): 目标路径

        """
        super().__init__()
        
        self.file_name = file_name
        self.opt = opt
        self.file_size = file_size
        self.s = socket
        self.dpath = dpath
        self.endEvent = Event()

        self.init_ui()
        self.init_signals()
        return

    def init_ui(self) -> None:
        """初始化界面

        根据选项更改窗口标题
        """
        if self.opt == 'download':
            self.setWindowTitle(f'下载:{self.file_name}')
        else:
            self.setWindowTitle(f'上传:{self.file_name}')
        return
    
    def init_signals(self) -> None:
        """初始化信号
        """
        self.btn_cancel.clicked.connect(self.on_cancel_clicked)
        return

    
    def start(self) -> None:
        """开始进行传输

        根据选项不同，新建上传/下载线程，绑定信号，开始传输
        """
        if self.opt == 'download':
            self.progressBar.setMaximum(self.file_size)
            self.th_dl = Th_dl(self.s, self.file_size, self.endEvent)
            self.th_dl.progress_update.connect(self.on_progress_updated)
            self.th_dl.finished.connect(self.on_download_finished)
            self.th_dl.start()
        else:
            with open(self.dpath, 'rb') as f:
                buf = f.read()
            self.progressBar.setMaximum(len(buf))
            self.th_ul = Th_ul(self.s, buf, self.endEvent)
            self.th_ul.progress_update.connect(self.on_progress_updated)
            self.th_ul.finished.connect(self.on_upload_finished)
            self.th_ul.start()
        return
    
    def on_progress_updated(self, i:int) -> None:
        """更新进度条槽函数

        Args:
            i (int): 已经完成的大小（字节）
        """
        self.progressBar.setValue(i)
        return

    def on_cancel_clicked(self) -> None:
        """取消点击槽函数

        点击取消后，停止线程，关闭窗口
        """
        self.endEvent.set()
        self.close()
        return

    def on_download_finished(self, b:bytes) -> None:
        """下载完成槽函数

        下载线程结束后该函数执行，将得到的数据写入文件

        Args:
            b (bytes): 下载的文件数据
        """
        with open(self.dpath, 'wb') as f:
            f.write(b)
        self.btn_cancel.setText('完成')
        return

    def on_upload_finished(self) -> None:
        """上传完成槽函数

        上传线程结束后该函数执行
        """
        self.btn_cancel.setText('完成')
        return
    

    #---------------------------------------------------------------#
    # 以下两个方法为重写的PyQt事件处理器                               #
    # 当窗口出现特定行为时，以下方法被自动调用                          #
    # 重写没有影响原本的功能                                          #
    # 重写后增加了一个功能：在窗口打开时自动开始执行，关闭时自动停止线程  #
    #---------------------------------------------------------------#
    @override
    def showEvent(self, a0: QShowEvent | None) -> None:
        self.start()
        return super().showEvent(a0)
    @override
    def closeEvent(self, a0: QCloseEvent | None) -> None:
        self.endEvent.set()
        return super().closeEvent(a0)

