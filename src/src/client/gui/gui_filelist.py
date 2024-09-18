""" 文件界面的UI模块

Classes:
    GUI_Filelist(QWidget): 文件界面的UI类

"""

from typing             import override

from PyQt5.QtCore       import Qt
from PyQt5.QtGui        import QIcon
from PyQt5.QtWidgets    import QWidget, QLineEdit, QVBoxLayout, QPushButton, QHBoxLayout, QTableWidget



class GUI_Filelist(QWidget):
    """文件界面的UI类

    实现UI的绘制，没有任何功能
    """
    @override
    def __init__(self):
        super().__init__()
        self.resize(1200, 900)
        self.setWindowTitle('文件')
        layout = QVBoxLayout()
        self.setWindowIcon(QIcon('resource/icon.svg'))


        btn_layout = QHBoxLayout()
        self.btn_flush = QPushButton('\u21BB')
        self.btn_home = QPushButton('\u2302')
        self.btn_upper = QPushButton('\u21A5')
        
        self.btn_flush.setFixedSize(60, 60)
        self.btn_home.setFixedSize(60, 60)
        self.btn_upper.setFixedSize(60, 60)

        self.btn_upload = QPushButton('上传')
        self.btn_download = QPushButton('下载')
        filePath = QLineEdit()
        filePath.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self.btn_upload.setFixedHeight(60)
        self.btn_download.setFixedHeight(60)
        filePath.setFixedHeight(60)

        btn_layout.addWidget(self.btn_flush)
        btn_layout.addWidget(self.btn_home)
        btn_layout.addWidget(self.btn_upper)
        btn_layout.addWidget(filePath)
        btn_layout.addWidget(self.btn_upload)
        btn_layout.addWidget(self.btn_download)

        fileList = QTableWidget()

        layout.addLayout(btn_layout)
        layout.addWidget(fileList)
        self.setLayout(layout)

        self.list = fileList
        self.list.setColumnCount(4)
        self.list.setHorizontalHeaderLabels(('文件名', '文件类型', '文件大小', '修改时间'))
        self.list.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignLeft)
        
        self.list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.list.setVerticalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        self.list.setHorizontalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)

        self.list.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.list.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.list.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.list.verticalHeader().setVisible(False)
        self.list.setColumnWidth(0, 600)
        self.list.setColumnWidth(3, 400)

        self.pathbar = filePath
        return
    

    # 将地址栏映射为属性，便于获取和修改
    @property
    def path(self):
        return self.pathbar.text()
    @path.setter
    def path(self, s):
        self.pathbar.setText(s)
        return


# coding时保留的入口，用于显示窗口
# 运行当前文件可以直接查看窗口样式
if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    app = QApplication([])
    s = GUI_Filelist()
    s.show()
    app.exec()
