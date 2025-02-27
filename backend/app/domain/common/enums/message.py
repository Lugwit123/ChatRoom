from enum import IntEnum, EnumMeta
from typing import Dict, Any, Type, Union

def enum_to_dict(enum_class: Union[Type[IntEnum], EnumMeta]) -> Dict[str, Any]:
    """将枚举类转换为字典格式
    
    Args:
        enum_class: 要转换的枚举类
    
    Returns:
        Dict[str, Any]: {
            "values": {name: value},  # 名称到值的映射
            "labels": {value: name},  # 值到名称的映射
            "descriptions": {value: description}  # 值到描述的映射
        }
    """
    values = {}
    labels = {}
    descriptions = {}
    
    # 获取枚举类的所有成员
    for name, member in enum_class.__members__.items():
        values[name] = member.value
        labels[member.value] = name
    
    # 获取枚举类的文档字符串
    if enum_class.__doc__:
        doc_lines = enum_class.__doc__.split('\n')
        current_value = None
        for line in doc_lines:
            line = line.strip()
            if line.startswith('Attributes:'):
                continue
            if ':' in line:
                name = line.split(':', 1)[0].strip()
                if name in enum_class.__members__:
                    current_value = enum_class.__members__[name].value
            elif line and current_value is not None:
                descriptions[current_value] = line.strip()
    
    return {
        "values": values,      # 用于前端 MessageType.system -> 1
        "labels": labels,      # 用于前端 1 -> "system"
        "descriptions": descriptions  # 用于前端显示描述文本
    }

class MessageType(IntEnum):
    """用于定义消息在系统中的类型和用途。
    
    Attributes:
        chat:
            聊天消息，用户之间的对话
            
        system:
            系统消息，用于系统通知和提醒
        
        chat_history:
            聊天历史记录，用于显示历史消息
        
        validation:
            验证消息，用于用户身份验证
        
        user_list_update:
            用户列表更新消息，通知用户列表变化
        
        error:
            错误消息，用于显示错误信息
        
        get_users:
            获取用户列表消息，用于请求用户列表
        
        remote_control:
            远程控制消息，用于远程操作
        
        open_path:
            打开路径消息，用于打开文件或目录
    """
    chat = 1
    system = 2
    chat_history = 3
    validation = 4
    user_list_update = 5
    error = 6
    get_users = 7
    remote_control = 8
    open_path = 9

class MessageContentType(IntEnum):
    """消息内容类型枚举
    
    用于定义消息内容的格式类型。
    
    Attributes:
        rich_text:
            富文本消息，支持格式化文本
        
        url:
            超链接，网页链接
        
        audio:
            音频消息，语音或音乐
        
        image:
            图片消息，图片文件
        
        video:
            视频消息，视频文件
        
        file:
            文件消息，普通文件
        
        plain_text:
            纯文本消息，无格式文本
        
        user_list:
            用户列表，包含用户信息
        
        html:
            HTML内容，网页内容
    """
    rich_text = 1  # 富文本消息
    url = 2        # 超链接
    audio = 3      # 音频
    image = 4      # 图片
    video = 5      # 视频
    file = 6       # 文件
    plain_text = 7 # 纯文本
    user_list = 8  # 用户列表
    html = 9       # HTML内容

class MessageStatus(IntEnum):
    """消息状态枚举
    
    用于标识消息的当前状态。
    
    Attributes:
        unread:
            未读状态，消息尚未被接收者阅读
        
        read:
            已读状态，消息已被接收者阅读
        
        sending:
            发送中状态，消息正在发送
        
        sent:
            已发送状态，消息已成功发送
        
        delivered:
            已送达状态，消息已到达接收者
        
        success:
            发送成功状态，完整的发送流程已完成
        
        failed:
            发送失败状态，消息发送失败
        
        deleted:
            已删除状态，消息已被删除
        
        recalled:
            已撤回状态，消息已被发送者撤回
        
        unknown:
            未知状态，消息状态无法确定
    """
    unread = 1
    read = 2
    sending = 3
    sent = 4
    delivered = 5
    success = 6
    failed = 7
    deleted = 8
    recalled = 9
    unknown = 10

class MessageTargetType(IntEnum):
    """消息目标类型枚举
    
    用于定义消息的发送目标类型。
    
    Attributes:
        user:
            用户消息，发送给特定用户
        
        group:
            群组消息，发送给群组内所有成员
            
        broadcast:
            广播消息，发送给所有在线用户
            
        all:
            全体消息，发送给所有用户（包括离线用户）
    """
    user = 1
    group = 2

class MessageDirection(IntEnum):
    """消息方向枚举
    
    用于定义消息的发送方向。
    
    Attributes:
        response:
            响应消息，服务器发送给客户端
        
        request:
            请求消息，客户端发送给服务器
    """
    response = 1
    request = 2
    unknown = 3

class RemoteControlResponseStatus(IntEnum):
    """远程控制响应状态枚举
    
    用于定义远程控制请求的响应状态。
    
    Attributes:
        accepted:
            接受远程控制请求
        
        rejected:
            拒绝远程控制请求
    """
    wait_server_return_message_id = 1
    accepted = 2
    rejected = 3


class RemoteControlResponse:
    """远程控制响应结构
    
    用于定义远程控制响应的数据结构。
    
    Attributes:
        status (RemoteControlResponseStatus): 响应状态
        reason (str): 响应原因
        nickname (str): 响应用户昵称
        ip (str): 响应用户IP地址
    """
    def __init__(self, status: RemoteControlResponseStatus, reason: str, nickname: str, ip: str):
        self.status = status
        self.reason = reason
        self.nickname = nickname
        self.ip = ip
        
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式
        
        Returns:
            Dict[str, Any]: 字典格式的响应数据
        """
        return {
            'status': self.status.name,
            'reason': self.reason,
            'nickname': self.nickname,
            'ip': self.ip
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RemoteControlResponse':
        """从字典创建响应对象
        
        Args:
            data (Dict[str, Any]): 字典格式的响应数据
            
        Returns:
            RemoteControlResponse: 响应对象
        """
        status = RemoteControlResponseStatus.accepted if data['status'] == 'accepted' else RemoteControlResponseStatus.rejected
        return cls(
            status=status,
            reason=data['reason'],
            nickname=data['nickname'],
            ip=data['ip']
        )

def get_all_enums() -> Dict[str, Dict[str, Any]]:
    """获取所有枚举的定义
    
    Returns:
        Dict[str, Dict[str, Any]]: 所有枚举的定义
    """
    return {
        "MessageType": enum_to_dict(MessageType),
        "MessageContentType": enum_to_dict(MessageContentType),
        "MessageStatus": enum_to_dict(MessageStatus),
        "MessageTargetType": enum_to_dict(MessageTargetType),
        "MessageDirection": enum_to_dict(MessageDirection)
    }