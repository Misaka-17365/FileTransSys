""" 登录界面的UI模块

Classes:
    IP_Edit(QWidget): IP输入框
    CUI_Login(QWidget): 文件对话界面的UI类

"""

from typing             import override

from PyQt5.QtCore       import Qt, QRegExp
from PyQt5.QtGui        import QRegExpValidator, QIntValidator, QFont, QIcon
from PyQt5.QtWidgets    import QWidget, QGridLayout, QLabel, QLineEdit, QVBoxLayout, QPushButton, QHBoxLayout


class IP_Edit(QWidget):
    """IP 输入框

    为了解决IP输入不美观不方便的问题，设计一个IP输入框
    """

    @override
    def __init__(self) -> None:
        """重写初始化方法

        绘制界面
        """
        super().__init__()
        layout = QHBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        seg:list[QLineEdit] = []
        for i in range(4):
            k = QLineEdit()
            k.setAlignment(Qt.AlignmentFlag.AlignCenter)
            seg.append(k)
            layout.addWidget(k)
            if i != 3:
                layout.addWidget(QLabel('.'))
        self.setLayout(layout)
        for i in seg:
            i.setValidator(QRegExpValidator(QRegExp(r'(2((5[0-5])|([0-4][0-9])))|(1[0-9]{2})|([1-9][0-9]?)|0')))
        self.seg = seg
        return
    
    def setValue(self, ip:str) -> None:
        """设置值方法

        该方法可以使用合法的IP字符串设置输入框的值

        Args:
            ip (str): 合法的IP地址字符串（IPv4）
        """
        segs = ip.split('.')
        for i,j in zip(self.seg, segs):
            i.setText(j)
        return
    
    def text(self) -> str:
        """获取字符方法

        方法名与QLineEdit的方法名相同
        
        可以用与QLineEdit相同的方法操作

        Returns:
            str: IP地址字符串
        """
        segs = []
        for i in self.seg:
            k = i.text()
            if k == '':
                return ''
            segs.append(k)
        return '.'.join(segs)



class GUI_Login(QWidget):
    """登录界面的UI类

    实现UI的绘制，没有任何功能
    """
    @override
    def __init__(self) -> None:
        super().__init__()
        self.setFixedSize(800,600)
        self.setWindowTitle('登录')
        self.setWindowIcon(QIcon('resource/icon.svg'))

        self.submit = QPushButton('登录')
        self.search = QPushButton('搜索服务器')
        layout = QVBoxLayout()
        login_label = QLabel('文件系统登录')
        login_label.setFont(QFont(None, 20, 20, False))
        layout.addWidget(login_label, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.init_input())

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.search)
        btn_layout.addWidget(self.submit)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def init_input(self) -> QWidget:
        widget = QWidget()
        layout = QGridLayout()
        layout.addWidget(QLabel('服务器地址'), 0, 0)
        layout.addWidget(QLabel('服务器端口'), 2, 0)
        layout.addWidget(QLabel('用户名'), 4, 0)
        layout.addWidget(QLabel('密码'), 6, 0)

        self.hided_lables:list[QLabel] = []
        for i in range(4):
            k = QLabel(' ')
            k.setStyleSheet('color:red;font-weight:bold')
            self.hided_lables.append(k)
            layout.addWidget(k, 2*i+1, 1)

        self.input_ip   = IP_Edit()
        self.input_port = QLineEdit()
        self.input_id   = QLineEdit()
        self.input_pswd = QLineEdit()

        self.input_port.setValidator(QIntValidator(0, 65535))
        self.input_id.setValidator(QRegExpValidator(QRegExp(r'\w{0,32}')))

        layout.addWidget(self.input_ip, 0, 1)
        layout.addWidget(self.input_port, 2, 1)
        layout.addWidget(self.input_id, 4, 1)
        layout.addWidget(self.input_pswd, 6, 1)

        widget.setLayout(layout)
        return widget



# coding时保留的入口，用于显示窗口
# 运行当前文件可以直接查看窗口样式
if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    app = QApplication([])
    w = GUI_Login()
    w.show()
    app.exec()