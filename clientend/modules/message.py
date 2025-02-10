"""
消息相关的类和枚举定义
"""
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Union
from enum import Enum
from datetime import datetime

@dataclass
class MessageBase:
    """基础消息类型
    
    用于创建新消息的数据传输对象。
    
    Attributes:
        sender: 发送者用户名
        recipient: 接收者用户名
        content: 消息内容,可以是字符串或字典
        message_type: 消息类型,默认为聊天消息(1)
        target_type: 目标类型,默认为用户(1)
        content_type: 消息内容类型,默认为纯文本(7)
        status: 消息状态列表,默认为["pending"]
        timestamp: 消息时间戳,默认为当前时间
        reply_to_id: 回复的消息ID,可选
        popup_message: 是否弹出消息窗口
        extra_data: 额外数据字典
    """
    sender: str
    recipient: Optional[str] = None
    content: Union[str, Dict[str, Any]] = ""
    message_type: int = field(default=1)  # MessageType.chat
    target_type: int = field(default=1)  # MessageTargetType.user  
    content_type: int = field(default=7)  # MessageContentType.plain_text
    status: List[str] = field(default_factory=lambda: ["pending"])
    timestamp: Optional[str] = None
    reply_to_id: Optional[str] = None
    popup_message: bool = False
    extra_data: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """初始化后处理
        
        设置默认时间戳
        验证枚举值的合法性
        """
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
            
        # 验证枚举值
        valid_message_types = {1, 2, 3, 4, 5, 6, 7, 8, 9}  # MessageType枚举值
        valid_target_types = {1, 2, 3, 4}  # MessageTargetType枚举值
        valid_content_types = {1, 2, 3, 4, 5, 6, 7, 8, 9}  # MessageContentType枚举值
        
        if self.message_type not in valid_message_types:
            raise ValueError(f"Invalid message_type: {self.message_type}")
        if self.target_type not in valid_target_types:
            raise ValueError(f"Invalid target_type: {self.target_type}")
        if self.content_type not in valid_content_types:
            raise ValueError(f"Invalid content_type: {self.content_type}")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式
        
        Returns:
            Dict[str, Any]: 消息的字典表示
        """
        return {
            "sender": self.sender,
            "recipient": self.recipient,
            "content": self.content,
            "message_type": self.message_type,
            "target_type": self.target_type,
            "content_type": self.content_type,
            "status": self.status,
            "timestamp": self.timestamp,
            "reply_to_id": self.reply_to_id,
            "popup_message": self.popup_message,
            "extra_data": self.extra_data
        }
    
    def to_api_format(self) -> Dict[str, Any]:
        """转换为API请求格式
        
        Returns:
            Dict[str, Any]: 适用于API请求的消息格式
        """
        return {
            "content": self.content,
            "recipient_username": self.recipient,
            "content_type": self.content_type,
            "message_type": self.message_type,
            "target_type": self.target_type,
            "reply_to_id": self.reply_to_id,
            "extra_data": self.extra_data
        }

class MessageType(Enum):
    """消息类型枚举"""
    chat = 1
    system = 2
    chat_history = 3
    validation = 4
    user_list_update = 5
    error = 6
    get_users = 7
    remote_control = 8
    open_path = 9

class MessageTargetType(Enum):
    """消息目标类型枚举"""
    user = 1
    group = 2
    broadcast = 3
    all = 4

class MessageContentType(Enum):
    """消息内容类型枚举"""
    rich_text = 1
    url = 2
    audio = 3
    image = 4
    video = 5
    file = 6
    plain_text = 7
    user_list = 8
    html = 9

class EnumDefinition:
    """枚举定义类，用于动态创建枚举
    
    用于在运行时动态创建和管理枚举值，主要用于消息类型、目标类型等场景。
    
    Attributes:
        _values: 存储枚举名称到值的映射字典
    """
    def __init__(self, values: Dict[str, int]):
        self._values = values
        for name, value in values.items():
            setattr(self, name.lower(), value)
            
    def __getattr__(self, name: str) -> Any:
        if name.lower() in self._values:
            return self._values[name.lower()]
        raise AttributeError(f"'{self.__class__.__name__}' has no attribute '{name}'")
            
    @property
    def value(self) -> int:
        """兼容IntEnum的value属性"""
        return self._value if hasattr(self, '_value') else 0 