""" 数据包模块

Classse:
    Package(object): 数据包类

"""

import json 

class Package:
    '''
    用于控制信息的编码，实现服务端与客户端间控制信息交互

    每个 Package 实例需要一个包id，用以实现区分，请使用`get_id`方法获取唯一的id
    '''
    __used_id = 0
    def __init__(self, id:int, cmd:str, args:list) -> None:
        self.id = id
        self.cmd = cmd
        self.args =args
        return
    
    def to_bytes(self, encoding='utf-8') -> bytes:
        """将当前包的信息序列化
        使用json序列化为字符串，再编码成bytes

        Args:
            encoding (str, optional): 字符串的编码方式. Defaults to 'utf-8'.

        Returns:
            bytes: 编码后的字节流
                编码后会在原有数据的开头增加4字节的数据，用以标记该包的大小
        """
        tmp = {
            'id' : self.id,
            'cmd': self.cmd,
            'args': self.args
        }
        body = json.dumps(tmp).encode(encoding=encoding)
        length = len(body)
        head = length.to_bytes(4, 'big')
        return head + body
    
    @classmethod
    def from_bytes(self, b:bytes, encoding='utf-8') -> 'Package':
        """将字节流转为 Package 实例

        Args:
            b (bytes): 字节流
            encoding (str, optional): 字节流的编码方式. Defaults to 'utf-8'.

        Returns:
            Package: 生成的Package实例
        """
        tmp:dict = json.loads(b.decode(encoding=encoding))
        id = tmp.pop('id')
        cmd = tmp.pop('cmd')
        args = tmp.pop('args')
        return Package(id, cmd, args)
    
    @classmethod
    def get_id(cls) -> int:
        """生成一个唯一id

        Returns:
            int: 生成的唯一id
        """
        cls.__used_id += 1
        return cls.__used_id
    
