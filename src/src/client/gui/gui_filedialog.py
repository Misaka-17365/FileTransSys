""" 文件对话界面的UI模块

Classes:
    GUI_Filedialog(QWidget): 文件对话界面的UI类

"""

from typing             import override

from PyQt5.QtGui        import QIcon
from PyQt5.QtWidgets    import QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QProgressBar



class GUI_Filedialog(QWidget):
    """文件对话界面的UI类

    实现UI的绘制，没有任何功能
    """
    @override
    def __init__(self):
        super().__init__()
    
        self.resize(800, 300)
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.setWindowIcon(QIcon('resource/icon.svg'))

        self.progressBar = QProgressBar()
        self.progressBar.setTextVisible(True)

        self.btn_cancel = QPushButton('取消')
        btn_ly = QHBoxLayout()
        btn_ly.addWidget(self.btn_cancel)
        layout.addWidget(self.progressBar)
        layout.addLayout(btn_ly)

        return



# coding时保留的入口，用于显示窗口
# 运行当前文件可以直接查看窗口样式
if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    app = QApplication([])
    s = GUI_Filedialog()
    s.show()
    app.exec()
