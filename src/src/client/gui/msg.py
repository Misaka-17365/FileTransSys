""" 消息界面模块

Classes:
    Msg(src.client.gui.gui_msg.GUI_Msg): 消息界面类

"""

from typing import override

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QCloseEvent

from .gui_msg import GUI_Msg


class Msg(GUI_Msg):
    """消息界面类

    实现消息界面的全部功能

    Signals:
        submitted: 发送消息信号，携带(msg)
    """
    submitted = pyqtSignal(str)
    __display_append = pyqtSignal(str)

    # -------------------------------- 初始化 ----------------------------------
    @override
    def __init__(self) -> None:
        """重写初始化方法

        调用初始化信号方法
        """
        super().__init__()
        self.init_signals()
        return

    def init_signals(self) -> None:
        """初始化信号

        将所有的信号与槽连接
        """
        self.send.clicked.connect(self.on_submit_clicked)
        self.__display_append.connect(self.on_display_append)
        return

    # --------------------------------- 槽函数 ----------------------------------

    def on_submit_clicked(self) -> None:
        """发送点击槽函数

        当发送按键点击时，执行该函数

        将输入栏中的字符串拿出，触发submitted信号，清空输入栏
        """
        t = self.edit.toPlainText()
        self.submitted.emit(t)
        self.edit.clear()
        return
    
    def on_display_append(self, s:str) -> None:
        """更新消息显示窗口槽函数

        绑定在 __display_addpend 信号上，用以实现 apend 方法

        Args:
            s (str): 需要添加的字符串
        """
        self.display.append(s+'\n')
        return


    # ------------- 显示接口 --------------

    def append(self, s:str) -> None:
        """向显示窗口写入字符串的方法

        Args:
            s (str): 要显示的字符串

        在这里解释一下为什么要 调用方法->发射信号->执行槽函数 的过程更新窗口

        PyQt不允许在主线程之外的地方修改界面，
        因此所有界面处理必须放在主线程中，即丢到Qt事件循环当中进行。

        使用触发信号的方式，事件循环会执行槽函数

        将界面的更改放在槽函数当中，即可正确修改界面

        再对信号的发射进行包装，包装成普通方法，就成了如上的过程
        """
        self.__display_append.emit(s)
        return
    

    #---------------------------------------------------------------#
    # 以下方法为重写的PyQt事件处理器                                  #
    # 当窗口出现特定行为时，以下方法被自动调用                          #
    # 重写后窗口关闭事件被拦截，窗口关闭变为隐藏                        #
    #---------------------------------------------------------------#
    @override
    def closeEvent(self, a0: QCloseEvent | None) -> None:
        a0.ignore()
        self.hide()
        return
