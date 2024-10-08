文件传输系统
===

[TOC]

---

# 1 系统内交互规范

本节阐明系统内各个组成部分的交互过程，不涉及具体的数据格式。

具体数据格式参考[常量与方法定义](#常量与方法定义)


## 1.1 客户端内部交互

### 1.1.1 客户端核心
客户端核心封装了`socket`类，根据交互规范，提供了一套 **线程安全** 的阻塞式API，图形界面（GUI）以异步形式调用该API来实现与服务端交互

#### 实现方法

客户端核心（以下简称核心）内部维护了一个发送队列和一个接收表，来实现一个socket多线程使用。核心内部有两个线程——发送线程和接收线程。发送线程会读取当前发送队列中的数据包，将其写入到socket；接收线程不断读取socket，将接收到的数据还原成数据包，并放在接收表当中。下面的传输过程描述解释了核心的工作流程——即如何实现线程安全。

当一个API被调用时，该函数执行以下几个操作：
1. 对应参数被打包成标准传输数据包
2. 获取该数据包的`id`，在接收表中注册接收信息
3. 将该数据包放入发送队列
4. 等待接收线程将接收的数据包放入表对应的位置
5. 删除接收表的注册信息
6. 返回接收的结果

由于socket的发送和接收由单独一个线程占用，因此在发送和接受数据上是安全的。核心与发送/接收线程的交互通过队列/带锁的表，因此也是线程安全的。

**注册 & 接收**
函数在获取数据包`id`后，将该`id`作为key，在接收表中添加结束事件和返回值的容器。当接收线程接收到该`id`的数据包时，将该数据包放入返回值容器并触发结束事件。

### 1.1.2 客户端GUI




---

## 1.2 服务端内部交互

### 1.2.1 工作者线程

工作者线程是处理客户端请求的线程。每一个工作者线程处理一个客户端的连接。

工作者线程由管理者线程拉起，可由管理者线程关闭。

工作者线程完成以下功能：
- 登录
- 权限管理
- 消息获取与推送
- 文件列表获取
- 文件上传与下载

工作者线程在开始后，会拉起另外两个线程，接收线程和发送线程，这两个线程负责将接收请求包并解码，编码并发送响应包。

#### 处理客户端请求

接收线程会接收来自客户端的数据，将该数据解码并生成原本的`Package`格式，添加到待处理队列当中。

工作者线程从队列中获取请求包，开始处理该请求，并使用处理结果生成响应包，添加到待发送队列当中。

发送线程从待发送队列当中获取响应包，将该包编码发送给客户端。

#### 询问管理者线程

当 用户登录/推送消息 时，工作者线程向管理者线程询问。工作者线程开始阻塞等待管理者线程处理询问。



### 1.2.2 管理者线程

管理者线程是服务器的主线程，管理所有工作者线程，并负责对用户登录记录、用户权限记录以及消息分发。

管理者线程在开始后会自动拉起一个监听线程，该线程负责监听新的TCP连接。当一个新的TCP连接产生时，监听线程将该`socket`对象放入到队列当中。

管理者线程在一个循环当中完成以下任务：
- 处理新的TCP连接
- 响应工作者线程的询问
- 向工作者线程分发消息

#### 处理新连接

当队列中有新的TCP连接时，产生一个新的工作者线程来处理该连接的请求。

#### 回复询问

工作者线程的询问有两种：**登录** 和 **消息推送**。

登录请求：管理者线程需要验证ID和密码是否正确，是否有客户端已经使用该ID和密码登录，随后给工作者线程正确的回复。

消息推送：管理者线程将该消息添加到列表中，在[分发消息](#分发消息)阶段分发给每一个已登录的工作者线程。

#### 分发消息

管理者线程收集服务端和客户端的消息，将所有消息依次放入工作者线程的消息缓冲队列 `msgBuf`中。

---

## 1.2 客户端与服务端交互

### 1.2.1 请求

当客户端与服务端建立一个TCP连接后，客户端通过该TCP连接向服务端发送控制请求，例如发送**请求文件列表**或**请求文件下载**等控制命令。

随后，服务端通过该TCP连接向客户端返回一个状态，该状态包含对应请求所需的全部信息。

> 注意：服务端是无状态的，即每一次请求与下一次请求之间无关联
>
> 注意：当请求与文件的 **上传/下载** 相关时，仅返回状态码和相关端口号，并非返回请求的数据。


### 1.2.2 响应

每当客户端的一个请求被服务端接受时，服务端开始处理，处理后将结果通过响应包返回给客户端。

如果服务端收的请求格式不符合要求，则服务端不会返回任何信息。

---


# 2 常量与方法定义

本节阐述系统中不同部分交互的数据格式，不涉及各个部分的交互过程。

交互的具体过程参见[系统内交互规范](#系统内交互规范)

---

## 2.1 客户端内定义

待补充

---

## 2.2 服务端内定义

以下为服务器内部的通信格式



### 2.2.1 服务器配置

用来配置服务器的参数

这些参数由 `ServerConfig` 类的类属性定义，详见[这里](#serverconfig-类)



### 2.2.2 消息

工作者线程与管理者线程之间，对消息进行包装

`msg(user_id, time, string)`

- `user_id` 为消息发送者的ID
- `time` 为结构化的时间 `(year, month, day, hour, minute, second)` 
- `string` 为消息内容字符串



### 2.2.3 询问

工作者线程向管理者线程询问，结构如下

`(cmd:str, args:list, finish:Event, retval:list)`

- `cmd` 向管理者线程请求的内容
- `args` 请求的参数
- `finish` 完成信号，当管理者线程完成响应后，该信号被触发
- `retval` 接收返回值的容器，管理者线程将请求的结果放入该列表

`cmd(args)->(retval)` 可以有以下值：

- `user(user_id, user_passwd)->(code, user_info)` 
  请求用户信息
- `msg(msg)->(code)`  
  请求推送消息 参数 `msg` 为[消息](#消息)




## 2.3 客户端与服务端交互接口

客户端与服务端控制端口的通信格式

请求格式和响应格式的编解码已经由 `Package` 类实现，详见[这里](#package-类)


#### 请求格式

使用 `json` 作为请求的格式，具体格式如下

```json
{
	"id"	: <id  :int>,
	"cmd"	: <cmd :str>,
	"args"	: <args:list>
}
```

请求为一个 `json` 对象，包含三个键值对。

- `id` 用来对请求进行编号
  每一个请求有唯一的整数编号，用来区分不同请求，以匹配对应的返回信息
- `cmd` 用来传输请求的[命令](#请求命令)
- `args` 用来传输该请求对应的[参数](#请求命令)


#### 响应格式

使用 `json` 作为响应的格式，具体格式如下

```json
{
	"id"	: <id  :int>,
	"cmd"	: "return",
	"args"	: [
			<code:int>,
			<data:any> 
		  ]
}
```

响应为一个 `json` 对象，包含三个键值对。

- `id` 对应于请求包的ID
- `cmd` 恒为字符串 `"return"`
- `args` 为返回的数据
  - `state` 本次请求的[状态码](#状态码)
  - `addon` 本次请求的[附加数据](#附加数据)



#### 请求支持的命令

支持的命令 `cmd(args)`：

- `login(user_id, user_passwd)` - 请求登录
  - `user_id` string: 登录用户的ID
  - `user_passwd` string: 登录用户的密码

- `getFileList(dir_path)` - 获取文件列表
  - `dir_path` string: 获取文件列表的目录
  
- `getMessage()` - 获取消息
- `putMessage(msg)` - 推送消息
  - `msg` string: 消息内容
  
- `getFile(file_path, begin_byte)`
  - `file_path` string: 服务端的文件路径
  - `begin_byte` int: 从该位置开始读取文件（支持断点续传）
  
- `putFile(file_path:str, file_size:int)`
  - `file_path` string: 服务端的文件路径（上传位置）
  - `file_size` int: 该文件的实际大小



#### 状态码

可能返回的 `code`

| 错误类型 | 错误码 | 解释 |
|---|---|---|
|SUCCESS                 	|  0	|成功
|ERR_NO_LOGIN            	|201	|未登录
|ERR_USER_UNDEFINED      	|202	|无该用户
|ERR_PSWD_UNMATCH        	|203	|密码错误
|ERR_NO_PERMISSION       	|204	|无权限
|ERR_USER_RELOGIN        	|205	|用户重登录
|ERR_FILE_NOT_EXIST      	|301 	|文件不存在
|ERR_FIEL_ALREADY_EXIST  	|302	|文件已经存在
|ERR_DIR_NOT_EXIST			|303	|文件夹不存在
|ERR_DIR_ALREADY_EXIST		|304	|文件夹已经存在
|ERR_SERVER_BUSY         	|401	|服务器忙
|ERR_UNDEf_CMD				|501	|未知命令

以上定义在 `StatCode` 类中，详见[这里](#statcode-类)



#### 附加数据

当响应成功时，`data` 附带的数据类型
> 响应错误时，附带的数据类型未定义

- `login` 
  -  `None`
  
- `getFileList` 
  -  `([dir,...],[file,...])`   
  一个元组，包含两个元素，第一个元素是该目录下所有目录，第二个元素是该目录下所有文件  
  `file` 为四个元素的元组 `(文件名， 文件类型， 文件大小， 修改时间)`
  
- `getMessage` 
  -  `List[(user_id, time, message)]`  
  一个列表，包含0~n个元组，每个元组由**用户ID** **发送时间** **消息内容** 三部分组成。
  `time` 为结构化时间，一个元组`(year, month, day, hour, minute, second)`
- `putMessage` 
  -  `None`

- `getFile` 
  -  `(port, file_size)`

- `putFile` 
  -  `(port)`


---


# 3 系统中定义的类

## 3.1 全局类

---

### 3.1.1 StatCode 类

参见[源代码](../src/defs/statcode.py)

`StatCode` 类不可实例化，该类的类属性定义了响应的状态码

---

### 3.1.2 Package 类

参见[源代码](../src/defs/package.py)

`Packgae` 类实现了对控制命令的生成、编码和解码

#### 发送命令

使用参数实例化 `Package` 类，使用`to_bytes`方法进行打包编码，生成字节流，再使用`socket`发送该字节流。

示例：

```python
# 请求文件列表 getFileList('.')
pkg = Package(Package.get_id(), "getFileList", ['.'])
sbuf = pkg.to_bytes()
socket.sendall(sbuf)

# 请求下载文件 getFile('sample.txt', 0)
pkg = Package(Package.get_id(), "getFile", ["sample.txt", 0])
sbuf = pkg.to_bytes()
socket.sendall(sbuf)
```

#### 接收命令

每个`Package`在编码后，会在头部添加4个字节大小的整型数据，用来标识该包的大小。

首先接收4个字节的数据，还原出数据包的大小，然后再接收整个数据包，使用 `Package` 类提供的方法`from_bytes`解析该字节流为数据包。

示例：

```python
plen = int.from_bytes(socket.recv(4))
buf = socket.recv(plen)
pkg = Package.from_bytes(buf)
```

> 注意：以上示例当中默认 `socket.recv` 方法可以一次性获取到全部数据，在实际应用时需要通过其他手段保证完整接收数据


---

## 3.2 客户端类

---

## 3.3 服务端类

---

### 3.3.1 ServerConfig 类

参见[源代码](../src/server/serverconfig.py)

`ServerConfig` 类不能实例化，该类通过类属性来控制服务器的运行模式。

---

### 3.3.2 UserInfo 类

参见[源代码](../src/server/userinfo.py)

`UserInfo` 类实现对用户信息的存储和解析

#### 实例属性

#### 实例方法

#### 类方法

---

### 3.3.3 Master 类

---

### 3.3.4 Worker 类

---

