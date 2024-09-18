文件传输系统
===

---

# 使用方法

## 客户端

运行 client_launch.py 文件


## 服务端

服务端有两种界面，命令行和图形界面

### 命令行

命令行的服务端启动器为 `server_launch.py`

命令行界面的服务端使用方法如下：
1. 编辑当前目录写的 `config.jsonc` 文件  
   文件不存在则运行一次程序，将自动生成一个默认的配置文件
2. 配置用户列表文件  
   该文件应与 `config.jsonc` 文件中 `userlistFile` 项相同  
   不存在则在当前目录自动创建一个默认的用户列表文件
3. 再次启动程序

### 图形界面

命令行的服务端启动器为 `server_launch_gui.py`

图形界面的服务端使用方法如下：
1. 准备好用户列表文件
2. 打开软件，配置所有选项
3. 点击启动

---

# 文件格式

**注意：所有文件的编码均为gb2312格式，使用UTF-8会出现错误**

## 配置文件 `config.jsonc`

配置文件格式如下
```json
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
```

## 用户列表文件 `userlist.csv`

用户列表文件的格式如下:
```csv
用户名, 密码, 获取消息权限, 推送消息权限, 下载文件权限, 上传文件权限
tsang,123,1,1,1,1
t,123,1,0,1,0
```

第一行默认为表头，不解析

用户名和密码均为可见字符串。权限配置中 1 或 true表示允许，0 或 false表示拒绝。自动忽略空行。禁止不完整的行，将会报出格式错误。

---