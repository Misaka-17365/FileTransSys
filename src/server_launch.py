""" 服务端入口（CUI）

运行该文件即可启动服务端（CUI）

通过配置文件 config.jsonc 来控制服务端的行为

无动态权限管理，无消息发送和接收功能
"""

import os
import sys
import time
import json5
import logging
from   pathlib import Path
import socket

from   src.server.ipbroadcast import Th_broadcast
from   src.server import Master, UserInfo, ServerConfig


def load_userlist(filepath:str) -> list:
    """加载用户列表

    Args:
        filepath (str): 用户列表文件路径（需要csv文件）

    Returns:
        list: 用户信息列表
    """

    retval = []
    with open(filepath, 'r') as f:      # 如果编码报错，尝试更换成 'utf-8' 或者 'gbk' 编码
        f.readline()
        lines = f.readlines()
    for i in lines:
        if i.strip() == '':
            continue
        retval.append(UserInfo.from_str(i))
    return retval


def load_config(filepath:str) -> dict:
    """加载配置文件

    Args:
        filepath (str): 配置文件路径

    Returns:
        dict: 包含配置信息的字典
    """

    with open(filepath, 'r') as f:    # 如果编码报错，尝试更换成 'utf-8' 或者 'gbk' 编码
        cfg = json5.load(f)
    return cfg


def init_logger(cfg:dict) -> logging.Logger:
    """初始化 logger

    Args:
        cfg (dict): 配置字典

    Returns:
        logging.Logger: 初始化完成的 logger
    """

    logger = logging.getLogger('main_logger')
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(fmt='[%(asctime)s] <%(levelname)s> %(message)s')

    # 这里实例化两个 handler，一个用来向文件输出，另一个向标准错误输出
    file_handle = logging.FileHandler(filename=cfg['logPath'], mode='a', encoding='utf-8')  # 如果编码报错，尝试更换成 'utf-8' 或者 'gbk' 编码
    file_handle.setFormatter(formatter)
    file_handle.setLevel(logging.INFO)
    console_handle = logging.StreamHandler()
    console_handle.setFormatter(formatter)
    console_handle.setLevel(logging.INFO)
    logger.addHandler(file_handle)
    logger.addHandler(console_handle)
    logger.info(f'Logger 初始化完成')
    return logger



def gen_default_config_file():
    """生成默认的配置文件

    当配置文件不存在时，默认在当前目录生成一个配置文件
    """

    with open('./config.jsonc', 'w') as f:
        f.write('''
{
    // 服务器配置
    "name": "SERVER-1",
    "ip": "0.0.0.0",
    "port": "9000",

    // 用户权限总设置
    "permission": {
        // 消息权限
        "allUserGetMessage": true,
        "allUserPutMessage": false,
        "distributeMessage": true,
        // 文件权限
        "allUserGetFilelist": true,
        "allUserDownloadFile": true,
        "allUserUploadFile": false
    },
    // 共享文件夹路径
    "shareDir": "./public",
    // 用户列表文件路径(.csv文件)
    "userlistFile": "./userlist.csv",

    // 日志输出路径
    "logPath": "./server.log",

    // 开启服务器IP地址广播
    "ipBroadcast": true
}
''')

def gen_default_userlist():
    """生成默认的用户列表文件

    当用户列表文件不存在时，默认在当前目录生成一个用户列表文件
    """

    with open('./userlist.csv', 'w') as f:
        f.write('''用户名, 密码, 获取消息权限, 推送消息权限, 下载文件权限, 上传文件权限
default_user, 1234, 1, 1, 1, 0
                
''')


def configurate_server(cfg:dict):
    """更改 ServerConfig 的配置

    Args:
        cfg (dict): 配置字典
    """
    ServerConfig.SHARE_DIR = Path(cfg['shareDir']).absolute()
    ServerConfig.PERMISSION.update(cfg['permission'])
    return


def start_server(cfg:dict, userlist:list):
    """启动服务器

    Args:
        cfg (dict): 配置字典
        userlist (list): 用户信息列表

    由于主线程不能退出，这个函数不会返回

    这个函数应该最后一个调用
    """
    m = Master((cfg['ip'], int(cfg['port'])), userlist)
    m.start()
    if cfg['ipBroadcast']:
        broadcast = Th_broadcast(cfg['name'], socket.gethostbyname(socket.gethostname()), m.s.getsockname()[1])
        broadcast.start()
    while True:
        time.sleep(100)





def main():
    if not Path('./config.jsonc').exists():
        with open('./readme.tmp.txt', 'w') as f:
            f.write('配置文件不存在\n')
            f.write('默认配置文件已生成，请修改配置，重新启动服务器\n')
            f.write('请在命令行窗口启动该软件')
        gen_default_config_file()
        return

    cfg = load_config('./config.jsonc')
    userlistFile = cfg['userlistFile']
    if not Path(userlistFile).exists():
        gen_default_userlist()
        print('用户列表解析失败：文件不存在')
        print('默认用户列表已生成')
        sys.exit()
    try:
        userlist = load_userlist(userlistFile)
    except:
        print('用户列表解析失败：文件格式不正确')
        sys.exit()

    if not Path(cfg['shareDir']).exists():
        print('共享文件夹不存在')
        return

    ServerConfig.log = init_logger(cfg)

    configurate_server(cfg)
    start_server(cfg, userlist)

if __name__ == '__main__':
    main()