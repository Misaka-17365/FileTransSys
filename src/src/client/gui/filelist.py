""" 文件界面模块

Classes:
    Filelist(src.client.gui.gui_filelist.GUI_Filelist): 文件界面类

"""


from   typing           import override
import time

from   PyQt5.QtCore     import pyqtSignal
from   PyQt5.QtGui      import QCloseEvent
from   PyQt5.QtWidgets  import QTableWidgetItem
from   .gui_filelist    import GUI_Filelist




class Filelist(GUI_Filelist):
    """文件界面类

    实现文件界面的全部功能

    Signals:
        filelist_required: 请求文件列表，携带(dir_path)
        upload_required: 请求上传文件，携带(dir_path)
        download_required: 请求下载文件，携带(file_path)
    """
    filelist_required   = pyqtSignal(str)       # 文件夹路径
    __updated           = pyqtSignal(tuple)     # (路径, [文件夹名], [文件(文件名, 类型, 大小, 修改时间)])
    upload_required     = pyqtSignal(str)       # 文件夹路径
    download_required   = pyqtSignal(str)       # 文件路径


    # --------------------------- 初始化 -------------------------------

    @override
    def __init__(self) -> None:
        """重写初始化方法

        初始化默认路径为 /

        调用信号初始化
        """
        super().__init__()
        self.path = '/'
        self.last_list = None
        self.init_signals()
        return

    def init_signals(self) -> None:
        """信号初始化

        将信号与信号槽连接
        """
        self.__updated.connect(self.on_updated)
        self.btn_flush      .clicked.connect(self.on_flush_clicked)
        self.btn_home       .clicked.connect(self.on_home_clicked)
        self.btn_upper      .clicked.connect(self.on_upper_clicked)
        self.btn_download   .clicked.connect(self.on_download_clicked)
        self.btn_upload     .clicked.connect(self.on_upload_clicked)
        self.list.cellDoubleClicked.connect(self.on_tablecell_doubleClicked)
        return

    # ----------------------------- 槽函数 ------------------------------

    def on_flush_clicked(self) -> None:
        """刷新按钮点击槽函数
        """
        self.filelist_required.emit(self.path)
        return
    
    def on_home_clicked(self) -> None:
        """根目录按钮点击槽函数
        """
        self.path = '/'
        self.filelist_required.emit(self.path)
        return
    
    def on_upper_clicked(self) -> None:
        """上级按钮点击槽函数
        """
        # 通过字符串操作，解析出上一级目录的路径
        current_path = self.path
        if current_path == '/':
            pass
        else:
            i = current_path[:-1].rfind('/')
            self.path = current_path[:i+1]
        self.filelist_required.emit(self.path)
        return
    
    def on_download_clicked(self) -> None:
        """下载按钮点击槽函数

        下载逻辑由 on_tablecell_doubleClicked 实现，本方法是该方法的包装
        """
        self.on_tablecell_doubleClicked(self.list.currentItem().row(), 0)
        return
    
    def on_tablecell_doubleClicked(self, row:int, colume:int) -> None:
        """文件双击槽函数

        Args:
            row (int): 点击的行坐标
            colume (int): 点击的列坐标

        实现文件下载请求信号的发射
        """
        name = self.list.item(row, 0).text()
        type = self.list.item(row, 1).text()
        if type == '文件夹':
            # 如果是文件夹，则进入该文件夹
            self.filelist_required.emit(self.path+name+'/')
        else:
            # 如果是文件，则发射请求下载信号
            self.download_required.emit(self.path + name)
        return
    
    def on_upload_clicked(self) -> None:
        """文件上传按钮点击槽函数
        """
        self.upload_required.emit(self.path)
        return
    
    def on_updated(self, t:tuple) -> None:
        """文件列表更新槽函数

        连接到 __updated 信号，实现文件列表的更新

        Args:
            t (tuple): 文件夹列表与文件列表的元组
        """

        # 检测是否和上一次更新时相同，相同则无需更新，直接返回
        if t == self.last_list:
            return
        self.last_list = t

        path  = t[0]        # 路径
        dirs  = t[1]        # 文件夹列表
        files = t[2]        # 文件列表
        self.list.setRowCount(0)    # 清空原列表
        self.list.clearContents()
        row_count = 0
        
        self.path = path    # 设置当前路径为路径

        for i in dirs:      # 添加文件夹到列表
            self.list.insertRow(row_count)
            self.list.setItem(row_count, 0, QTableWidgetItem(i))
            self.list.setItem(row_count, 1, QTableWidgetItem('文件夹'))
            row_count += 1

        def sizeFmt(size:int) -> str:
            """格式化文件大小函数

            Args:
                size (int): 文件大小(字节)

            Returns:
                str: 标识大小的字符串
            """
            if size < 2**12:
                return str(size)+' Byte'
            elif size < 2**20:
                return '%2.1f kiB'%(size/2**10)
            elif size < 2**30:
                return '%2.1f MiB'%(size/2**20)
            elif size < 2**40:
                return '%2.1f GiB'%(size/2**30)
            else:
                return '%2.1f TiB'%(size/2**40)

        for i in files:     # 添加文件到列表
            self.list.insertRow(row_count)
            self.list.setItem(row_count, 0, QTableWidgetItem(i[0]))
            self.list.setItem(row_count, 1, QTableWidgetItem(i[1]))
            self.list.setItem(row_count, 2, QTableWidgetItem(sizeFmt(i[2])))
            self.list.setItem(row_count, 3, QTableWidgetItem(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(i[3]))))
            row_count += 1
        return


    # -------------------------------- 接口 --------------------------------------
    def update(self, t:tuple) -> None:
        """更新文件列表的方法

        Args:
            t (tuple): 包含文件夹列表和文件列表的元组
        """
        self.__updated.emit(t)
        return
    
    #---------------------------------------------------------------#
    # 以下方法为重写的PyQt事件处理器                                  #
    # 当窗口出现特定行为时，以下方法被自动调用                          #
    # 重写后窗口关闭事件被拦截，窗口关闭变为隐藏                        #
    #---------------------------------------------------------------#
    @override
    def closeEvent(self, a0: QCloseEvent | None) -> None:
        self.hide()
        a0.ignore()
        return
