""" 消息界面的UI模块

Classes:
    GUI_Msg(QWidget): 消息界面的UI类

"""

from typing             import override
from PyQt5.QtGui        import QIcon
from PyQt5.QtWidgets    import QWidget, QVBoxLayout, QPushButton, QTextBrowser, QTextEdit

class GUI_Msg(QWidget):
    """消息界面的UI类

    实现UI的绘制，没有任何功能
    """
    @override
    def __init__(self):
        super().__init__()        
        self.setWindowTitle('消息')
        self.resize(600, 900)
        self.setWindowIcon(QIcon('resource/icon.svg'))
        self.init_ui()
        return
    
    def init_ui(self):
        layout = QVBoxLayout()
        self.display = QTextBrowser()
        self.edit = QTextEdit()
        self.send = QPushButton('发送')
        layout.addWidget(self.display, 7)

        layout.addWidget(self.edit,2)
        layout.addWidget(self.send, 1)
        self.setLayout(layout)
        return


# coding时保留的入口，用于显示窗口
# 运行当前文件可以直接查看窗口样式
if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    app = QApplication([])
    s = GUI_Msg()
    s.show()
    app.exec()