from typing import Literal


class UserInfo:
    def __init__(self, id:str, passwd:str, permission:tuple[bool, bool, bool, bool]) -> None:
        ''' 初始化一个 `用户信息`

        Args:
            id: str user_id
            passwd: str user_password
            permission: tuple[msg_down, msg_up, file_down, file_up] 
        '''
        if not isinstance(id, str):
            raise TypeError
        if not isinstance(passwd, str):
            raise TypeError
        if not isinstance(permission, tuple) and not isinstance(permission, list):
            raise TypeError
        if len(permission) != 4:
            raise ValueError('length of permission should be 4')
        for i in permission:
            if not isinstance(i, bool):
                raise TypeError
            continue

        self.id = id
        self.passwd = passwd

        self.per_msg_d = permission[0]
        self.per_msg_u = permission[1]
        self.per_file_d = permission[2]
        self.per_file_u = permission[3]
        return
    
    @classmethod
    def from_str(cls, s:str) -> 'UserInfo':
        '''使用字符串生成一个 `用户信息`

        Args:
            s: 一个包含用户信息的字符串，
                user_id user_passwd per_msg_d per_msg_u per_file_d per_file_u \n
                其中用空白字符分隔
        '''
        tokens = s.split()
        if len(tokens) != 6:
            raise ValueError(f'Length of tokens should be 6, given {len(tokens)}')
        per = []
        for i in tokens[2:]:
            per.append(bool(i))
        return UserInfo(tokens[0], tokens[1], per)
    

