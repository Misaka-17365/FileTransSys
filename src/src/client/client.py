""" 客户端的整合逻辑模块

即客户端的完整模块，包含客户端设计的全部

Classes:
    Client(QWidget): 客户端类

"""

from typing             import override
import time
from threading          import Thread, Lock, Event
from pathlib            import Path

from PyQt5.QtCore       import pyqtSignal
from PyQt5.QtWidgets    import QWidget, QApplication, QMessageBox, QFileDialog, QSystemTrayIcon

from .gui               import Login, Msg, Filelist, Filedialog, GUI_Tray
from ..client.core      import ErrCode, ClientCore


class Client(QWidget):
    """客户端类

    一个完整的客户端实现
    """
    __logined   = pyqtSignal()
    __logouted  = pyqtSignal()
    __show_msg  = pyqtSignal(str)


    # ------------------------ 初始化 ----------------------------

    @override
    def __init__(self) -> None:
        """重写初始化方法

        初始化窗口、信号和子窗口、托盘图标
        """
        super().__init__()

        self.user_id = ''
        self.logined = False

        self.cc = ClientCore()      # 核心逻辑
        self.w_login = Login()      # 登录界面
        self.tray = GUI_Tray()      # 系统托盘

        self.init_ui()
        self.init_signals()
        self.tray.show()
        self.w_login.show()
        return
    
    def init_signals(self) -> None:
        """初始化信号连接

        注意：消息窗口和文件窗口的信号不在此处连接，
        因为此时还没有创建这两个窗口，
        这两个窗口的创建和信号连接将在登陆后进行

        """
        # 内部状态改变信号的连接
        self.__logined.connect(self.on_logined)
        self.__logouted.connect(self.on_logouted)
        self.__show_msg.connect(self.on_show_msg_emitted)
        # 登录信号的连接
        self.w_login.submitted.connect(self.on_wLogin_submitted)
        # 托盘的信号连接
        self.tray.actions['登录'].triggered.connect(self.w_login.show)
        self.tray.actions['退出'].triggered.connect(self.quit)
        self.tray.activated[QSystemTrayIcon.ActivationReason].connect(self.on_tray_actived)
        return
    
    def init_ui(self) -> None:
        """初始化界面的行为

        将托盘的菜单中[消息]和[文件]两个选项禁用，因为此时没有登录
        """
        self.tray.actions['登录'].setEnabled(True)
        self.tray.actions['登录'].setText(f'登录')
        self.tray.actions['消息'].setEnabled(False)
        self.tray.actions['文件'].setEnabled(False)
        return
    

    # --------------------------- 槽函数 -- 处理窗口信号 -------------------------------

    def on_wLogin_submitted(self, t:tuple) -> None:
        """登录窗口 submitted 信号槽

        Args:
            t (tuple): 登录信息

        这个信号槽函数是阻塞的
        """

        ok = self.cc.connect(t[0:2])
        if not ok:
            self.showMsg('服务器连接失败')
            return
        del ok
        err = self.cc.login(t[2], t[3])
        if err[0]:
            self.showMsg(f'登录失败\n错误代码:{err[0]}')
            self.cc.close()             # 如果连接成功但登录失败，默认断开连接
            return
        self.user_id = t[2]
        self.__logined.emit()
        return

    def on_wMsg_submitted(self, s:str) -> None:
        """消息窗口 submitted 信号槽

        Args:
            s (str): 消息
        """
        def func():
            code, _ = self.cc.putMessage(s)
            if code == ErrCode.SUCCESS:
                ...
            elif code == ErrCode.ERR_NO_LOGIN:
                self.__logouted.emit()
            else:
                self.showMsg(f'发送消息失败\n错误代码:{code}')
        Thread(target=func).start()
        return
    
    def on_wFilelist_filelistRequired(self, dir:str) -> None:
        """文件窗口 filelist_required 信号槽

        Args:
            dir (str): 请求文件列表的路径
        """
        def func():
            code, lst = self.cc.getFileList(dir)
            if code == ErrCode.SUCCESS:
                self.w_filelist.update((dir, lst[0], lst[1]))
            elif code == ErrCode.ERR_NO_LOGIN:
                self.__logouted.emit()
            else:
                self.showMsg(f'获取文件列表失败\n错误代码:{code}')
        Thread(target=func).start()
        return

    def on_wFilelist_uploadRequired(self, dst:str) -> None:
        """文件窗口 upload_required 信号槽

        Args:
            dst (str): 上传的目标路径

        这个信号槽函数是阻塞的
        """

        # 使用列表来保存 dialog 窗口
        if not hasattr(self, 'dialogs'):
            self.dialogs_lock = Lock()
            self.dialogs:list[QFileDialog] = []
        src, _ = QFileDialog.getOpenFileName(None, '保存文件', '', None, None, QFileDialog.Options())
        if src == '':       # 文件选择取消后会返回空字符串，此时取消上传
            return
        
        # 获取必要的信息
        src= Path(src)
        file_size = src.stat().st_size
        file_name = src.name

        # 调用核心API
        # 注意这里自动将文件重命名，便于标识上传者和上传时间
        err, addon = self.cc.putFile(dst+f'{self.user_id+time.strftime('%Y%m%d%H%M%S')}_'+file_name, file_size)
        if err:
            self.showMsg(f'文件上传失败\n错误代码:{err}')
            return
        # 将得到的socket传给文件对话界面
        dialog = Filedialog(dst+f'{self.user_id+time.strftime('%Y%m%d%H%M%S')}_'+file_name, 'upload', 0, addon[0], src)
        # 清理已关闭的 dialogs
        with self.dialogs_lock:
            dead_map = []
            for i in self.dialogs:
                if i.isHidden():
                    dead_map.append(i)
            for i in dead_map:
                self.dialogs.remove(i)
        
        self.dialogs.append(dialog)     # 添加新的 dialog 到列表
        dialog.show()                   # 启动 dialog
        return

    def on_wFileList_downloadRequired(self, src:str) -> None:
        """文件窗口 download_required 信号槽

        Args:
            src (str): 下载的目标文件路径

        这个信号槽函数是阻塞的
        """

        # 使用列表来保存 dialog 窗口
        if not hasattr(self, 'dialogs'):
            self.dialogs_lock = Lock()
            self.dialogs:list[QFileDialog] = []
        dst, _ = QFileDialog.getSaveFileName(None, '保存文件', src.split('/')[-1], None, None, QFileDialog.Options())
        if dst == '':           # 文件选择取消后会返回空字符串，此时取消下载
            return
        
        # 调用核心API，获取socket
        err, addon = self.cc.getFile(src, 0)
        if err:
            self.showMsg(f'文件下载失败\n错误代码:{err}')
            return
        # 新建文件对话界面，将socket传入
        dialog = Filedialog(src, 'download', addon[1], addon[0], dst)
        # 清理
        with self.dialogs_lock:
            dead_map = []
            for i in self.dialogs:
                if i.isHidden():
                    dead_map.append(i)
            for i in dead_map:
                self.dialogs.remove(i)
        self.dialogs.append(dialog)         # 添加到列表
        dialog.show()                       # 启动
        return

    def on_tray_actived(self, reason:QSystemTrayIcon.ActivationReason) -> None:
        """托盘图标激活槽函数

        Args:
            reason (QSystemTrayIcon.ActivationReason): 激活原因

        双击托盘显示所有窗口
        """
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            if hasattr(self, 'w_filelist'):
                self.w_filelist.show()
            if hasattr(self, 'w_msg'):
                self.w_msg.show()
        return
        
    

    # --------------------------- 槽函数 -- 登录状态改变 ------------------------------

    def on_logined(self) -> None:
        """登录状态改变槽函数：登录

        负责处理登录后的一系列初始化，包括新窗口的创建和界面的改变等
        """

        self.logined = True             # 登录状态标记
        self.w_msg = Msg()              # 新建消息窗口
        self.w_filelist = Filelist()    # 新建文件窗口
        self.tray.setIconLogin(True)    # 设定托盘为已登录图标
        
        self.w_login.hide()             # 隐藏登录界面
        self.w_filelist.show()          # 显示文件界面
        self.w_msg.show()               # 显示消息界面

        # 控制托盘的行为
        self.tray.actions['登录'].setEnabled(False)
        self.tray.actions['登录'].setText(f'已登录：{self.user_id}')
        self.tray.actions['消息'].setEnabled(True)
        self.tray.actions['文件'].setEnabled(True)
        self.tray.actions['消息'].triggered.connect(self.w_msg.show)
        self.tray.actions['文件'].triggered.connect(self.w_filelist.show)

        # 连接新窗口的信号
        self.w_msg.submitted.connect(self.on_wMsg_submitted)
        self.w_filelist.filelist_required.connect(self.on_wFilelist_filelistRequired)
        self.w_filelist.upload_required.connect(self.on_wFilelist_uploadRequired)
        self.w_filelist.download_required.connect(self.on_wFileList_downloadRequired)

        self.start_getMsg()             # 启动自动获取消息
        self.start_getFilelist()        # 启动自动刷新文件列表
        return

    def on_logouted(self) -> None:
        """登录状态改变槽函数：登出

        负责处理登出后的一系列初始化
        """

        self.logined = False            # 登录状态标记
        self.w_login.show()             # 显示登陆界面
        self.tray.setIconLogin(False)   # 设置托盘图标为未登录图标

        # 控制托盘行为
        self.tray.actions['登录'].setEnabled(True)
        self.tray.actions['登录'].setText(f'登录')
        self.tray.actions['消息'].setEnabled(False)
        self.tray.actions['文件'].setEnabled(False)

        # 取消关联信号
        self.w_msg.submitted.disconnect(self.on_wMsg_submitted)
        self.w_filelist.filelist_required.disconnect(self.on_wFilelist_filelistRequired)
        self.w_filelist.upload_required.disconnect(self.on_wFilelist_uploadRequired)
        self.w_filelist.download_required.disconnect(self.on_wFileList_downloadRequired)

        # 删除消息窗口和文件窗口
        if hasattr(self, 'w_msg'):
            self.w_msg.close()
            del self.w_msg
        if hasattr(self, 'w_filelist'):
            self.w_filelist.close()
            del self.w_filelist

        # 停止两个自动刷新的线程
        if hasattr(self, 'stopEvent'):
            self.stopEvent.set()
        return
    
    # ------------ 自动获取新消息 ------------
    
    def start_getMsg(self):
        """开启自动刷新消息

        通过开启一个线程实现定期自动获取新消息实现

        线程函数同样具有格式化消息的功能
        """

        # 初始化结束信号
        if not hasattr(self, 'stopEvent'):
            self.stopEvent = Event()
        self.stopEvent.clear()

        def func():
            while self.logined and not self.stopEvent.is_set():
                time.sleep(0.2)     # 用以减少服务器和网络负载
                # 获取消息
                code, lst_msg = self.cc.getMessage()
                if code == ErrCode.SUCCESS:
                    for i in lst_msg:
                        id = i[0]
                        time_ = i[1]
                        string = i[2]
                        stime_ = f'{time_[0]:4}-{time_[1]:02}-{time_[2]:02} {time_[3]:02}:{time_[4]:02}:{time_[5]:02}'
                        self.w_msg.append(f'[{stime_}]  {id}\n{string}')    # 写入消息显示框
                elif code == ErrCode.ERR_NO_LOGIN:
                    self.__logouted.emit()
        Thread(target=func).start()     # 启动线程
        return
    
    def start_getFilelist(self) -> None:
        """开启自动刷新文件列表

        通过开启一个线程实现定期自动发射请求信号 filelist_required 实现
        """

        # 初始化结束信号
        if not hasattr(self, 'stopEvent'):
            self.stopEvent = Event()
        self.stopEvent.clear()

        def f():
            stat = 0
            while self.logined and not self.stopEvent.is_set():
                # 两秒钟刷新一次，但为了加快程序退出时间，延时不能太大，这里使用状态机来实现
                time.sleep(0.5)     
                stat += 1
                if stat == 4:
                    stat = 0
                    self.w_filelist.filelist_required.emit(self.w_filelist.path)
        Thread(target=f, daemon=True).start()
        return

    
    def quit(self) -> None:
        """客户端的退出方法

        绑定在托盘的退出选项上

        清理所有开启的资源，然后退出事件循环
        """
        if hasattr(self, 'dialogs'):        # 删除所有文件对话界面
            for i in self.dialogs:
                if i.isVisible(): i.activateWindow(); return
        self.cc.close()                     # 关闭核心
        self.stopEvent.set()                # 关闭自动刷新的线程
        QApplication.instance().quit()      # 退出事件循环
        return


    #-------------------------------------------#
    # 以下两个方法是为了实现任意线程内弹出消息框    #
    # 调用 showMsg 方法来弹出一个消息框           #
    # 类的工具方法                               #
    #-------------------------------------------#
    def showMsg(self, msg:str):
        self.__show_msg.emit(msg)
    def on_show_msg_emitted(self, s:str):
        QMessageBox.information(None, '提示', f'{s:<20}', QMessageBox.StandardButton.Close, QMessageBox.StandardButton.Close)
    



# coding时保留的入口，用于启动客户端
# 由于存在相对导入，直接执行会报错，建议使用启动文件执行
# 如需执行，请在Python 后添加 -m 参数
if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    app = QApplication([])
    w = Client()
    app.exec()
    