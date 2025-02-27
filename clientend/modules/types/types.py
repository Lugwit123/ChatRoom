from typing import Dict, Any, Optional, List, Union, TypedDict, Literal
from dataclasses import dataclass, field
from datetime import datetime
from enum import IntEnum

# 消息类型枚举
class MessageType(IntEnum):
    """用于定义消息在系统中的类型和用途。
    
    Attributes:
        chat: 聊天消息，用户之间的对话
        system: 系统消息，用于系统通知和提醒
        chat_history: 聊天历史记录，用于显示历史消息
        validation: 验证消息，用于用户身份验证
        user_list_update: 用户列表更新消息，通知用户列表变化
        error: 错误消息，用于显示错误信息
        get_users: 获取用户列表消息，用于请求用户列表
        remote_control: 远程控制消息，用于远程操作
        open_path: 打开路径消息，用于打开文件或目录
        abc_check: ABC检查消息，用于ABC检查反馈
        notification: 通知消息，用于通知用户
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
    abc_check = 10
    notification = 11

# 按钮配置类型
class ButtonConfig(TypedDict, total=False):
    """按钮配置类型
    
    Attributes:
        accept (str): 接受按钮文本
        reject (str): 拒绝按钮文本
        open (str): 打开按钮文本
        close (str): 关闭按钮文本
    """
    accept: str
    reject: str
    open: str
    close: str

# 按钮ID类型
ButtonId = Literal['accept', 'close']

# 拒绝理由预设选项
REJECT_REASONS = [
    "正在忙，无法接受远程控制",
    "正在开会，稍后再说",
    "设备状态不佳，不适合远程控制",
    "正在处理其他远程控制请求",
    "其他原因"
]

@dataclass
class RejectResponse:
    """拒绝响应数据类型
    
    Attributes:
        reason (str): 拒绝理由
        is_custom (bool): 是否是自定义理由
    """
    reason: str
    is_custom: bool = False

# 消息方向枚举
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

# 消息目标类型枚举
class MessageTargetType(IntEnum):
    """消息目标类型枚举"""
    user = 1
    group = 2
    broadcast = 3
    all = 4

# 消息内容类型枚举
class MessageContentType(IntEnum):
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

# 枚举定义类
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

@dataclass
class MessageBase:
    """基础消息类型
    
    Attributes:
        sender (str): 发送者用户名
        recipient (Optional[str]): 接收者用户名
        content (Union[str, Dict[str, Any]]): 消息内容
        timestamp (Optional[str]): 时间戳
        recipient_type (str): 接收者类型
        status (List[str]): 消息状态
        direction (str): 消息方向
        message_content_type (str): 消息内容类型
        message_type (MessageType): 消息类型
        popup_message (bool): 是否弹出消息
    """
    sender: str
    recipient: Optional[str] = None
    content: Union[str, Dict[str, Any]] = ""
    timestamp: Optional[str] = None
    recipient_type: str = "user"
    status: List[str] = field(default_factory=lambda: ["pending"])
    direction: str = "request"
    message_content_type: str = "plain_text"
    message_type: Union[MessageType, str, int] = MessageType.chat
    popup_message: bool = False
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
            
        # 处理消息类型
        if isinstance(self.message_type, (str, int)):
            try:
                # 如果是字符串，先尝试转换为整数
                if isinstance(self.message_type, str):
                    self.message_type = int(self.message_type)
                # 将整数转换为枚举值
                self.message_type = MessageType(self.message_type)
            except (ValueError, TypeError):
                # 如果转换失败，使用默认值
                self.message_type = MessageType.chat

@dataclass
class NotificationConfig:
    """通知窗口配置
    
    Attributes:
        message (MessageBase): 消息对象
        result (str): 结果
        image_path (Optional[str]): 图片路径
        button_config (Optional[ButtonConfig]): 按钮配置
        chat_signals (Optional[Any]): 聊天信号
        parent_window (Optional[Any]): 父窗口
    """
    message: MessageBase
    result: str = ""
    image_path: Optional[str] = None
    button_config: Optional[ButtonConfig] = None
    chat_signals: Optional[Any] = None
    parent_window: Optional[Any] = None

# 远程控制响应状态枚举
class RemoteControlResponseStatus(IntEnum):
    """远程控制响应状态枚举
    
    用于定义远程控制请求的响应状态。
    
    Attributes:
        wait_server_return_message_id:
            等待服务器返回消息ID
        
        accepted:
            接受远程控制请求
        
        rejected:
            拒绝远程控制请求
    """
    wait_server_return_message_id = 1
    accepted = 2
    rejected = 3

@dataclass
class RemoteControlResponse:
    """远程控制响应结构
    
    用于定义远程控制响应的数据结构。
    
    Attributes:
        status (RemoteControlResponseStatus): 响应状态
        reason (str): 响应原因
        nickname (str): 响应用户昵称
        ip (str): 响应用户IP地址
    """
    status: RemoteControlResponseStatus
    reason: str
    nickname: str
    ip: str
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式
        
        Returns:
            Dict[str, Any]: 字典格式的响应数据
        """
        return {
            'status': 'accepted' if self.status == RemoteControlResponseStatus.accepted else 'rejected',
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

# 默认按钮配置
DEFAULT_BUTTON_CONFIG: ButtonConfig = {
    'accept': '接受控制',
    'reject': '拒绝',
    'open': '打开',
    'close': '关闭'
}