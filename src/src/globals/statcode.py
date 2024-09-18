""" 状态码模块

Classes:
    StatCode(object): 状态码类

"""

class StatCode:
    '''
    StatCode 类用来规定 **网络请求** 的状态码

    规定 0 为成功

    1   ~ 199 为其他自定义错误保留

    200 ~ 299 为权限相关错误

    300 ~ 399 为文件相关错误

    400 ~ 499 为服务器内部错误
    '''
    SUCCESS                 = 0

    ERR_NO_LOGIN            = 201
    ERR_USER_UNDEFINED      = 202
    ERR_PSWD_UNMATCH        = 203
    ERR_NO_PERMISSION       = 204
    ERR_USER_RELOGIN        = 205

    ERR_FILE_NOT_EXIST      = 301
    ERR_FIEL_ALREADY_EXIST  = 302
    ERR_DIR_NOT_EXIST       = 303
    ERR_DIR_ALREADY_EXIST   = 304

    ERR_SERVER_BUSY         = 401
    ERR_UNDEF_CMD           = 501

