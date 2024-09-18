""" src.client.core.errcode

客户端的错误代码模块

Classes:
    ErrCode(src.globals.StatCode): 客户端的错误代码类

"""

from ...globals import StatCode

class ErrCode(StatCode):
    """客户端错误代码类

    继承于 src.globals.StatCode 类

    类属性为定义的错误类型及代码

    错误代码为整型(int)
    """
    ERR_TIME_OUT = 101
