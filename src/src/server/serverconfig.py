""" 服务器配置模块

模块提供了一个全局的ServerConfig类，使用类属性来存储服务器配置以实现动态修改服务器配置
"""


import logging
from pathlib import Path

class ServerConfig:
    # 共享文件夹路径
    SHARE_DIR = Path('./public').absolute()
    # 全局用户权限
    PERMISSION = {
        'allUserGetMessage': True, 
        'allUserPutMessage': False, 
        'distributeMessage': True,
        'allUserGetFilelist': True, 
        'allUserDownloadFile': True, 
        'allUserUploadFile': False
        }
    # 全局 logger
    log:logging.Logger = None
