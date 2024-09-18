""" 客户端入口

执行该文件以启动客户端
"""

import sys
from src.client.client import Client, QApplication


if __name__ == '__main__':
    app = QApplication([])
    c = Client()
    sys.exit(app.exec())

