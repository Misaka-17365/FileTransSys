""" 服务端入口（GUI）

本模块为服务端提供了图形界面，执行本文件即可启动服务端

本模块可以实现服务器的图形化配置，支持动态调整服务器的全局权限

支持服务器发送、接收消息

log 会实时显示在GUI当中

**注意** 关闭界面会自动关闭服务器
"""


import sys
import time
import socket
import re
from pathlib    import Path
from threading  import Thread
from typing     import override
import logging

from PyQt5.QtWidgets    import  QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QTextBrowser, \
                                QGroupBox, QLabel, QPushButton, QLineEdit, QCheckBox, QRadioButton, \
                                QTextEdit, QSizePolicy, \
                                QFileDialog
from PyQt5.QtGui        import  QCloseEvent, QTextCursor, QIcon
from PyQt5.QtCore       import  pyqtSignal

from src.server.serverconfig   import ServerConfig
from src.server.userinfo       import UserInfo
from src.server.ipbroadcast    import Th_broadcast
from src.server.master         import Master




class GUI_Server_UI(QMainWindow):
    """服务器界面的UI类

    完成服务器的UI绘制
    """

    @override
    def __init__(self) -> None:
        super().__init__(None)
        self.resize(1600,1000)
        self.setWindowIcon(QIcon('resource/icon.svg'))
        self.setWindowTitle('文件传输<服务端>')
        tab = QTabWidget()
        self.terminal = QTextBrowser()

        tab.addTab(self.init_tab_config(), '服务器配置')
        tab.addTab(self.init_tab_string(), '消息')
        tab.addTab(self.terminal,'日志')
        self.setCentralWidget(tab)
        self.show()
        return

    def init_tab_config(self) -> QWidget:
        """生成配置界面

        Returns:
            QWidget: 配置界面的布局
        """
        widgit = QWidget()
        layout = QVBoxLayout()

        # --------- BEGIN <STAT> --------------
        group_state = QGroupBox()
        layout_state = QHBoxLayout()
        self.config_state = QLabel('已关闭')
        self.config_on = QPushButton('开启')
        layout_state.addWidget(QLabel('当前状态'), 1)
        layout_state.addWidget(self.config_state,5)
        layout_state.addWidget(self.config_on,3)


        group_state.setLayout(layout_state)
        group_state.setTitle('状态')
        layout.addWidget(group_state)
        # ---------- END <STAT> ---------------

        # --------- BEGIN <IP PORT> ------------
        group_ip_port = QGroupBox()
        layout_ip_port = QHBoxLayout()
        self.config_ip = QLineEdit()
        self.config_port = QLineEdit()
        layout_ip_port.addWidget(QLabel('服务器IP'), 0)
        layout_ip_port.addWidget(self.config_ip, 1)
        layout_ip_port.addWidget(QLabel('监听端口'), 0)
        layout_ip_port.addWidget(self.config_port, 1)
        group_ip_port.setLayout(layout_ip_port)
        group_ip_port.setTitle('监听')
        layout.addWidget(group_ip_port)
        # --------- END <IP PORT> --------------

        # ----------- BEGIN <USER> -------------
        group_user = QGroupBox()
        layout_user = QHBoxLayout()
        self.config_userlist = QLineEdit()
        self.config_userlist_btn = QPushButton('浏览')
        layout_user.addWidget(QLabel('用户列表文件(*.csv)'))
        layout_user.addWidget(self.config_userlist)
        layout_user.addWidget(self.config_userlist_btn)

        group_user.setLayout(layout_user)
        group_user.setTitle('用户')
        layout.addWidget(group_user)
        # ----------- END <USER> --------------


        # ----------- BEGIN <STRING> ------------
        group_string = QGroupBox()
        layout_string = QHBoxLayout()
        self.config_msgFreeDL = QCheckBox('获取消息')
        self.config_msgFreeUL = QCheckBox('推送消息')
        self.config_msgServerOnly = QRadioButton('仅推送到服务端')
        self.config_msgUserAll = QRadioButton('推送到全部用户')
        layout_string.addWidget(QLabel('消息分发'))
        layout_string.addWidget(self.config_msgFreeDL)
        layout_string.addWidget(self.config_msgFreeUL)
        layout_string.addWidget(self.config_msgServerOnly)
        layout_string.addWidget(self.config_msgUserAll)

        group_string.setLayout(layout_string)
        group_string.setTitle('消息')
        layout.addWidget(group_string)
        # ------------ END <STRING> -------------

        # ------------ BEGIN <FILE> -------------
        group_file = QGroupBox()
        layout_file = QVBoxLayout()

        layout_fileFolder = QHBoxLayout()
        self.config_fileFolder = QLineEdit()
        self.config_fileFolder_btn = QPushButton('浏览')
        layout_fileFolder.addWidget(QLabel('共享文件夹'))
        layout_fileFolder.addWidget(self.config_fileFolder)
        layout_fileFolder.addWidget(self.config_fileFolder_btn)
        layout_file.addLayout(layout_fileFolder)

        layout_filePmsn = QHBoxLayout()
        self.config_fileFreeDL = QCheckBox('允许下载')
        self.config_fileFreeUL = QCheckBox('允许上传')
        layout_filePmsn.addWidget(QLabel('用户权限'))
        layout_filePmsn.addWidget(self.config_fileFreeDL)
        layout_filePmsn.addWidget(self.config_fileFreeUL)
        layout_file.addLayout(layout_filePmsn)

        group_file.setLayout(layout_file)
        group_file.setTitle('文件')
        layout.addWidget(group_file)
        # ------------ END <FILE> ---------------

        # ----------- BEGIN <LOG> -------------
        group_log = QGroupBox()
        layout_log = QHBoxLayout()
        self.config_log = QLineEdit()
        self.config_log_btn = QPushButton('浏览')
        layout_log.addWidget(QLabel('日志输出路径'))
        layout_log.addWidget(self.config_log)
        layout_log.addWidget(self.config_log_btn)

        group_log.setLayout(layout_log)
        group_log.setTitle('日志')
        layout.addWidget(group_log)
        # ----------- END <USER> --------------

        widgit.setLayout(layout)
        return widgit
    

    def init_tab_string(self) -> QWidget:
        """生成消息界面

        Returns:
            QWidget: 消息界面的布局
        """
        widgit = QWidget()
        layout = QVBoxLayout()
        self.string_display = QTextBrowser()
        self.string_input = QTextEdit()
        self.string_send = QPushButton('发送')
        self.string_send.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding))
        layout.addWidget(self.string_display,7)

        layout_string_input = QHBoxLayout()
        layout_string_input.addWidget(self.string_input,9)
        layout_string_input.addWidget(self.string_send,1)
        layout.addLayout(layout_string_input, 2)
        widgit.setLayout(layout)
        return widgit
    
   




class GUI_Server(GUI_Server_UI):
    """服务端界面的实现类

    实现了服务端的全部功能
    """

    __display_updated = pyqtSignal(str)
    __msg_gotten = pyqtSignal(tuple)

    @override
    def __init__(self) -> None:
        super().__init__()
        self.init_signals()
        self.init_default_cfg()
        self.terminal.clear()
        ServerConfig.log = self.init_logger(self.config_log.text())
        return
        
    
    def init_default_cfg(self) -> None:
        """初始化服务器的默认配置
        """
        self.config_ip.setText('0.0.0.0')
        self.config_port.setText('9000')
        self.config_userlist.setText('./userlist.csv')
        self.config_fileFolder.setText('./public')
        self.config_log.setText('./server.log')
        self.config_msgFreeDL.setChecked(True)
        self.config_msgFreeUL.setChecked(True)
        self.config_msgServerOnly.setChecked(True)
        self.config_fileFreeDL.setChecked(True)
        self.config_fileFreeUL.setChecked(False)
        return 
    
    def init_signals(self) -> None:
        """初始化所有信号连接
        """

        # 选择文件按钮
        self.config_userlist_btn.clicked.connect(self.on_userlist_btn_clicked)
        self.config_fileFolder_btn.clicked.connect(self.on_shareDir_btn_clicked)
        # 启动按钮
        self.config_on.clicked.connect(self.on_server_started)

        # 权限配置按钮
        self.config_msgFreeDL.toggled.connect(lambda: ServerConfig.PERMISSION.update({'allUserGetMessage':self.config_msgFreeDL.isChecked()}))
        self.config_msgFreeUL.toggled.connect(self.on_config_msgUL_toggled)
        self.config_msgServerOnly.toggled.connect(lambda: ServerConfig.PERMISSION.update({'distributeMessage':not self.config_msgServerOnly.isChecked()}))
        self.config_fileFreeDL.toggled.connect(lambda: ServerConfig.PERMISSION.update({'allUserDownloadFile':self.config_fileFreeDL.isChecked()}))
        self.config_fileFreeUL.toggled.connect(lambda: ServerConfig.PERMISSION.update({'allUserUploadFile':self.config_fileFreeUL.isChecked()}))

        # 消息发送按钮
        self.string_send.clicked.connect(self.on_msg_submitted)
        # 获取新消息
        self.__msg_gotten.connect(self.on_msgDisplay_updated)
        
        # 打印新log
        self.__display_updated.connect(self.on_self_display_updated)
        return


    def init_logger(self, logPath:str) -> logging.Logger:
        """初始化 logger

        Args:
            logPath (str): log 文件的输出路径

        Returns:
            logging.Logger: 初始化完成的 logger
        """

        logger = logging.getLogger('main_logger')
        logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter(fmt='[%(asctime)s] <%(levelname)s> %(message)s')

        # file_handle 用于输出到文件，console_handle用于输出到界面
        file_handle = logging.FileHandler(logPath, mode='a', encoding='utf-8')  # 如果编码报错，尝试更换成 'utf-8' 或者 'gbk' 编码
        file_handle.setFormatter(formatter)
        file_handle.setLevel(logging.INFO)
        # ***********************************************************************************#
        # 注意：这里将self作为参数传递给了 StreamHandler 作为初始化                              #
        # StreamHandler 需要一个文本的 IO stream 对象                                          #
        # self 实现了一个 write 方法，该方法可以将参数显示在 GUI 上                              #
        # 当 self 实现了这一方法后，self 即是 IO stream 的子类型 :: 详见 Python - duck_type     #
        # 这样便实现了 logger 的输出重定向                                                     #
        console_handle = logging.StreamHandler(self)                                         #
        # ***********************************************************************************#
        console_handle.setFormatter(formatter)
        console_handle.setLevel(logging.INFO)
        logger.addHandler(file_handle)
        logger.addHandler(console_handle)
        logger.info(f'Logger 初始化完成')
        return logger
    

    def on_server_started(self) -> None:
        """开始按钮点击槽函数

        首先对输入的合法性进行检验，然后启动服务器
        """
        userListPath = Path(self.config_userlist.text())
        if not (userListPath.exists() and userListPath.is_file()):
            ServerConfig.log.error('开启失败:用户列表文件不存在')
            return
        userlist = []
        with open(userListPath, 'r') as f:
            f.readline()
            lines = f.readlines()
        for i in lines:
            userlist.append(UserInfo.from_str(i))

        folderPath = Path(self.config_fileFolder.text())
        if not folderPath.exists():
            ServerConfig.log.error('开启失败:共享文件夹路径不存在')
            return
        ServerConfig.SHARE_DIR = folderPath

        ip = self.config_ip.text()
        ip_re = re.compile(r'^((2(5[0-5]|[0-4]\d))|[0-1]?\d{1,2})(\.((2(5[0-5]|[0-4]\d))|[0-1]?\d{1,2})){3}$')
        if not ip_re.match(ip):
            ServerConfig.log.error('开启失败:IP地址格式不错误')
            return
        try:
            port = int(self.config_port.text())
        except Exception:
            ServerConfig.log.error('开启失败:端口号格式错误')
            return
        if port > 65535 or port < 0:
            ServerConfig.log.error('开启失败:端口号超出范围')
            return
        
        self.config_state.setText('已开启')
        
        self.m = Master((ip, port), userlist)
        self.m.start()

        broadcast = Th_broadcast('SERVER', socket.gethostbyname(socket.gethostname()), self.m.s.getsockname()[1])
        broadcast.start()

        self.__set_config_enable(False)
        self.config_on.setChecked(False)
        self.start_getMsg()
        return
    

    def on_userlist_btn_clicked(self) -> None:
        """打开一个对话框选择文件
        """
        filePath, _ = QFileDialog.getOpenFileName(
            parent=self,
            caption='选择文件',
            directory='.',
            filter='*.csv',
            initialFilter='*.csv',
            options=QFileDialog.Options())
        self.config_userlist.setText(filePath)
        return

    def on_shareDir_btn_clicked(self) -> None:
        """打开一个对话框选择文件夹
        """
        folderPath = QFileDialog.getExistingDirectory(
            parent=self,
            caption='选择文件夹',
            directory='.',
            options=QFileDialog.Options()
        )
        self.config_fileFolder.setText(folderPath)
        return
    
    def on_msgDisplay_updated(self, t:tuple[str, time.struct_time, str]) -> None:
        """消息框更新槽函数

        将接收到的消息格式化，并显示在GUI上

        Args:
            t (tuple[str, time.struct_time, str]): 一条消息的元组
        """
        time_ = t[1]
        stime_ = f'{time_[0]:4}-{time_[1]:02}-{time_[2]:02} {time_[3]:02}:{time_[4]:02}:{time_[5]:02}'
        self.string_display.append(f'[{stime_}]  {t[0]}\n{t[2]}')
        self.string_display.moveCursor(QTextCursor.MoveOperation.End)
        return
    
    def on_msg_submitted(self) -> None:
        """消息发送槽函数

        将当前输入框内的字符读出，放入服务器等待发送，清空输入框
        """
        s = self.string_input.toPlainText()
        self.string_input.clear()
        self.m.sendMsg(s)
        return
    

    def on_config_msgUL_toggled(self) -> None:
        """消息获取按钮状态翻转槽函数

        消息获取按钮的翻转会影响服务端的全局权限和其他按钮的可用性
        """
        t = self.config_msgFreeUL.isChecked()
        ServerConfig.PERMISSION['allUserPutMessage'] = t
        self.config_msgServerOnly.setEnabled(t)
        self.config_msgUserAll.setEnabled(t)
        return
    

    def on_self_display_updated(self, s:str) -> None:
        """log显示的槽函数

        该函数不光会将log显示在GUI上，同时可以将关键字染色

        Args:
            s (str): log 字符串
        """
        s = s.replace('<INFO>', '<font color=blue><b>&lt;INFO&gt;</b></font><font color=black></font>')
        s = s.replace('<WARNING>', '<font color=orange><b>&lt;WARNING&gt;</b></font><font color=black></font>')
        s = s.replace('<ERROR>', '<font color=red><b>&lt;ERROR&gt;</b></font><font color=black></font>')
        self.terminal.append(s)
        self.terminal.moveCursor(QTextCursor.MoveOperation.End)
        return


    def write(self, s:str):
        """实现 write 方法以实现输出重定向

        具体参见 Python - duck_type

        Args:
            s (str): 写入的log字符串
        """
        self.__display_updated.emit(s)
        return
    

    def __set_config_enable(self, enable:bool):
        """一个用来控制按钮可用性的开关

        Args:
            enable (bool): 按钮是否可用
        """
        self.config_userlist.setEnabled(enable)
        self.config_userlist_btn.setEnabled(enable)
        self.config_fileFolder.setEnabled(enable)
        self.config_fileFolder_btn.setEnabled(enable)
        self.config_log.setEnabled(enable)
        self.config_ip.setEnabled(enable)
        self.config_port.setEnabled(enable)
        self.config_on.setEnabled(enable)
        return
   
    def start_getMsg(self):
        """开启自动获取消息的线程

        从队列中获取新消息，然后发射 __msg_gotten 信号
        """
        def getMsg():
            while True:
                msg = self.m.msgBufr.get()
                self.__msg_gotten.emit(msg)
        Thread(target=getMsg, daemon=True).start()
        return
    

    #---------------------------------------------------------------#
    # 以下方法为重写的PyQt事件处理器                                  #
    # 当窗口出现特定行为时，以下方法被自动调用                          #
    # 重写没有影响原本的功能                                          #
    # 重写后增加了一个功能：在窗口关闭时自动停止获取新消息               #
    #---------------------------------------------------------------#
    def closeEvent(self, a0: QCloseEvent | None) -> None:
        if hasattr(self, 'm'):
            self.m.stop()
        return super().closeEvent(a0)





if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    app = QApplication([])
    w = GUI_Server()
    sys.exit(app.exec())
    