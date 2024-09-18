""" 软件托盘的UI模块

Classes:
    GUI_Tray(QSystemTrayIcon): 软件托盘的UI类

"""

from typing             import override
from PyQt5.QtGui        import QIcon
from PyQt5.QtWidgets    import QSystemTrayIcon, QMenu, QAction

class GUI_Tray(QSystemTrayIcon):
    """软件托盘的UI类

    实现UI的绘制，没有任何功能
    """
    @override
    def __init__(self):
        super().__init__()
        self.setIcon(QIcon('resource/fig/unlogined.svg'))
        self.setToolTip('文件传输系统')
        self.init_menu()
        return

    def init_menu(self):
        MENU_ITEM = ('登录', '消息', '文件', '退出')
        self.menu = QMenu()
        self.menu.setMinimumWidth(240)

        self.actions:dict[str, QAction] = {}
        for i in MENU_ITEM:
            self.actions[i] = QAction(QIcon(f'resource/fig/{i}.svg'), i)

        for i in self.actions.values():
            self.menu.addAction(i)
        self.setContextMenu(self.menu)
        return
    
    def setIconLogin(self, logined:bool):
        if logined:
            self.setIcon(QIcon('resource/fig/logined.svg'))
        else:
            self.setIcon(QIcon('resource/fig/unlogined.svg'))
        return



# coding时保留的入口，用于显示窗口
# 运行当前文件可以直接查看窗口样式
# 注意，由于没有窗口，此程序只能通过杀死进程关闭
if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    app = QApplication([])
    s = GUI_Tray()
    s.show()
    app.exec()