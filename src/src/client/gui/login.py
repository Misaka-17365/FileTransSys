""" 登录界面模块

Classes:
    Login(src.client.gui.gui_login.GUI_Login)

"""

from typing import override

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui  import QCloseEvent

from .gui_login import GUI_Login
from .serverlist import ServerList



class Login(GUI_Login):
    """登录界面类

    实现登录界面全部功能的类

    继承于 src.client.gui.gui_login.GUI_Login

    Signals:
        submitted: 提交登录信息，携带(ip, port, user_id, user_passwd)

    """

    submitted = pyqtSignal(tuple)


    # ------------------------------ 初始化 -------------------------------

    @override
    def __init__(self) -> None:
        """重写初始化方法

        新建一个服务器列表窗口，初始化所有信号

        (debug)初始化默认值
        """
        super().__init__()
        self.w_serverlist = ServerList()
        self.init_signals()
        # self.init_default_value()
        return
    
    def init_default_value(self) -> None:
        """初始化默认值

        测试用，软件中没有实际使用
        """
        self.input_ip.setValue('127.0.0.1')
        self.input_port.setText('5009')
        self.input_id.setText('tsang')
        self.input_pswd.setText('123')
        return
    
    def init_signals(self) -> None:
        """初始化信号连接

        将所有需要连接的信号进行连接

        应该在 __init__ 方法调用后调用
        """
        self.input_port.returnPressed.connect(self.input_id.setFocus)
        self.input_id.returnPressed.connect(self.input_pswd.setFocus)
        self.input_pswd.returnPressed.connect(self.on_submit_clicked)
        self.submit.clicked.connect(self.on_submit_clicked)
        self.search.clicked.connect(self.on_search_clicked)
        self.w_serverlist.selected.connect(self.on_server_selected)
        self.w_serverlist.doubleClicked.connect(self.on_server_doubleClicked)
        return



    # ---------------------------------- 槽函数 -------------------------------------
    
    def on_submit_clicked(self) -> None:
        """登录点击槽函数

        当“登录”点击后执行

        检验输入是否符合规范，符合规范则发射 submitted 信号
        """
        # 获取输入的文本
        ip = self.input_ip.text()
        port = self.input_port.text()
        id = self.input_id.text()
        pswd = self.input_pswd.text()

        # 输入合法性检验
        if ip == '': self.hided_lables[0].setText('请输入正确的IP地址'); return
        else: self.hided_lables[0].setText(' ')

        if port.isdigit():
            port = int(port)
            if port < 0 or port > 65535: self.hided_lables[1].setText('端口号超出范围（0~65535）'); return
            else:  self.hided_lables[1].setText(' ')
        else: self.hided_lables[1].setText('端口号是一个整数（0~65535）'); return

        if id == '': self.hided_lables[2].setText('请输入用户名'); return
        else: self.hided_lables[2].setText(' ')

        if pswd == '': self.hided_lables[3].setText('请输入密码'); return
        else: self.hided_lables[3].setText(' ')
        
        # 合法输入发射信号
        self.submitted.emit( (ip, port, id, pswd) )
        return
    
    def on_search_clicked(self) -> None:
        """搜索点击槽函数

        点击后显示服务器列表窗口
        """
        self.w_serverlist.show()
        return
 
    def on_server_selected(self, addr:tuple) -> None:
        """服务器选中槽函数

        该槽函数连接到 ServerList.selected 信号，用于更新输入框内容

        Args:
            addr (tuple): 地址(ip, port)
        """
        self.input_ip.setValue(addr[0])
        self.input_port.setText(addr[1])
        return
    
    def on_server_doubleClicked(self) -> None:
        """服务器列表双击槽函数

        双击将关闭服务器列表窗口
        """
        self.w_serverlist.close()
        return
    

    #---------------------------------------------------------------#
    # 以下方法为重写的PyQt事件处理器                                   #
    # 当窗口出现特定行为时，以下方法被自动调用                          #
    # 重写没有影响原本的功能                                          #
    # 重写后增加了一个功能：在登录窗口关闭时，自动关闭服务器列表窗口      #
    #---------------------------------------------------------------#
    @override
    def closeEvent(self, a0: QCloseEvent | None) -> None:
        self.w_serverlist.close()
        return super().closeEvent(a0)





# coding时保留的入口，用于显示窗口
# 已废弃，不保证正常运行
if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    app = QApplication([])
    s = Login()
    s.show()
    app.exec()
