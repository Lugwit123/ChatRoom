"""用户相关的数据传输对象"""
import pdb
import traceback
from datetime import datetime
from typing import Optional, Dict, Any, List, Sequence
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field

from app.domain.common.enums.user import UserRole, UserStatusEnum
from app.domain.common.models.tables import User, Device
from app.utils.time_utils import format_datetime
from Lugwit_Module import lprint

class UserBase(BaseModel):
    """用户基础数据传输对象
    
    包含用户的基本信息。
    
    Attributes:
        username:
            用户名
            用户的登录名称
        
        email:
            电子邮箱
            用户的联系邮箱
        
        nickname:
            昵称
            用户的显示名称
        
        avatar_index:
            头像索引
            用户头像的索引值
        
        role:
            用户角色
            用户在系统中的角色
        
        extra_data:
            额外数据
            用户的其他补充信息
    """
    id: int
    username: str
    nickname: Optional[str] = None
    email: Optional[str] = None
    role: UserRole = UserRole.user
    avatar_index: int = 0
    status: UserStatusEnum = UserStatusEnum.normal
    extra_data: Dict[str, Any] = Field(default_factory=dict)
    
    @classmethod
    def from_internal(cls, user: User) -> "UserBase":
        """从内部模型转换为DTO"""
        return cls(
            id=int(str(getattr(user, 'id', 0))),
            username=str(getattr(user, 'username', '')),
            nickname=str(getattr(user, 'nickname', '')) or None,
            email=str(getattr(user, 'email', '')) or None,
            role=UserRole(int(str(getattr(user, 'role', UserRole.user)))),
            avatar_index=int(str(getattr(user, 'avatar_index', 0))),
            status=UserStatusEnum(int(str(getattr(user, 'status', UserStatusEnum.normal)))),
            extra_data=dict(getattr(user, 'extra_data', {})) or {}
        )

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: format_datetime
        }
        
    def get(self, key: str, default: Any = None) -> Any:
        """获取属性值，类似字典的 get 方法
        
        Args:
            key: 属性名
            default: 默认值
            
        Returns:
            Any: 属性值或默认值
        """
        return getattr(self, key, default)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return self.model_dump()

class UserResponse(UserBase):
    """用户响应数据传输对象
    
    用于API响应中返回用户信息。
    
    Attributes:
        id:
            用户ID
            用户的唯一标识符
        
        created_at:
            创建时间
            用户账号的创建时间
        
        updated_at:
            更新时间
            用户信息的最后更新时间
        
        last_login:
            最后登录时间
            用户最近一次登录的时间
        
        login_status:
            登录状态
            用户的当前登录状态
    """
    last_login: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    login_status: bool = False
    devices: List[Dict[str, Any]] = Field(default_factory=list)

    @classmethod
    def from_internal(cls, user: User) -> "UserResponse":
        """从内部用户模型创建响应DTO"""
        # 检查用户是否有在线设备
        devices = getattr(user, 'devices', [])
        is_logged_in = any(getattr(device, 'is_online', lambda: False)() for device in devices)
        
        # 安全地获取时间字段
        last_login = getattr(user, 'last_login', None)
        if isinstance(last_login, datetime):
            last_login = last_login
        else:
            last_login = None
            
        created_at = getattr(user, 'created_at', None)
        if isinstance(created_at, datetime):
            created_at = created_at
        else:
            created_at = None
            
        updated_at = getattr(user, 'updated_at', None)
        if isinstance(updated_at, datetime):
            updated_at = updated_at
        else:
            updated_at = None
            
        # 安全地获取其他字段
        nickname = str(getattr(user, 'nickname', '')) or None
        email = str(getattr(user, 'email', '')) or None
        extra_data = dict(getattr(user, 'extra_data', {})) or {}
        
        return cls(
            id=int(str(getattr(user, 'id', 0))),
            username=str(getattr(user, 'username', '')),
            nickname=nickname,
            email=email,
            role=UserRole(int(str(getattr(user, 'role', UserRole.user)))),
            avatar_index=int(str(getattr(user, 'avatar_index', 0))),
            status=UserStatusEnum(int(str(getattr(user, 'status', UserStatusEnum.normal)))),
            last_login=last_login,
            created_at=created_at,
            updated_at=updated_at,
            login_status=is_logged_in,
            devices=[{k: str(v) for k, v in device.to_dict().items()} for device in devices],
            extra_data=extra_data
        )

class UserBaseAndDevices(BaseModel):
    """用户基础信息和状态数据传输对象
    
    包含用户的基本信息和状态。
    
    Attributes:
        id:
            用户ID
            用户的唯一标识符
        
        created_at:
            创建时间
            用户账号的创建时间
        
        updated_at:
            更新时间
            用户信息的最后更新时间
        
        last_login:
            最后登录时间
            用户最近一次登录的时间
        
        login_status:
            登录状态
            用户的当前登录状态
        
        devices:
            设备列表
            用户的所有设备信息
    """
    id: int
    username: str
    nickname: Optional[str] = None
    avatar_index: int = 0
    role: UserRole = UserRole.user
    status: UserStatusEnum = UserStatusEnum.normal
    devices: List[Dict[str, Any]] = Field(default_factory=list)
    
    @classmethod
    def from_internal(cls, user: Optional[User]) -> Optional['UserBaseAndDevices']:
        """从内部用户模型创建用户基本信息和状态"""
        if not user:
            return None
            
        # 安全地获取字段
        nickname = str(getattr(user, 'nickname', '')) or None
        devices = getattr(user, 'devices', [])
            
        return cls(
            id=int(str(getattr(user, 'id', 0))),
            username=str(getattr(user, 'username', '')),
            nickname=nickname,
            avatar_index=int(str(getattr(user, 'avatar_index', 0))),
            role=UserRole(int(str(getattr(user, 'role', UserRole.user)))),
            status=UserStatusEnum(int(str(getattr(user, 'status', UserStatusEnum.normal)))),
            devices=[{k: str(v) for k, v in device.to_dict().items()} for device in devices]
        )

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: format_datetime
        }

class UserCreate(UserBase):
    """用户创建数据传输对象
    
    用于创建新用户时传递的数据。
    
    Attributes:
        password:
            密码
            用户的登录密码
    """
    password: str

class UserUpdate(BaseModel):
    """用户更新数据传输对象
    
    用于更新用户信息时传递的数据。
    
    Attributes:
        email:
            电子邮箱
            用户的联系邮箱
        
        nickname:
            昵称
            用户的显示名称
        
        password:
            密码
            用户的新密码
        
        avatar_index:
            头像索引
            用户头像的索引值
        
        extra_data:
            额外数据
            用户的其他补充信息
    """
    nickname: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    avatar_index: Optional[int] = None
    extra_data: Optional[Dict[str, Any]] = None

class UserMessageInfo(UserResponse):
    """用户消息信息数据传输对象
    
    用于传递用户的消息相关信息。
    
    Attributes:
        user_id:
            用户ID
            用户的唯一标识符
        
        username:
            用户名
            用户的登录名称
        
        nickname:
            昵称
            用户的显示名称
        
        avatar_index:
            头像索引
            用户头像的索引值
        
        unread_count:
            未读消息数
            与该用户相关的未读消息数量
        
        last_message:
            最后一条消息
            与该用户的最后一条消息
    """
    messages: List[Dict[str, Any]] = Field(default_factory=list, description="与当前登录用户的消息记录")

class UserMapInfo(BaseModel):
    """用户映射信息数据传输对象
    
    用于用户映射中的用户信息。
    
    Attributes:
        id: 用户ID
        username: 用户名
        nickname: 昵称
        avatar_index: 头像索引
        role: 用户角色
        login_status: 登录状态
        created_at: 创建时间
        updated_at: 更新时间
        last_login: 最后登录时间
        extra_data: 额外数据
        devices: 设备列表
        messages: 消息列表
    """
    id: int
    username: str
    nickname: Optional[str] = None
    avatar_index: int = 0
    role: UserRole = UserRole.user
    login_status: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    extra_data: Dict[str, Any] = Field(default_factory=dict)
    devices: List[Dict[str, Any]] = Field(default_factory=list)
    messages: List[Dict[str, Any]] = Field(default_factory=list, description="与当前登录用户的消息记录")
    
    @classmethod
    def from_internal(cls, user: Optional[User]) -> Optional['UserMapInfo']:
        """从内部用户模型创建用户映射信息"""
        if not user:
            return None
            
        # 检查用户是否有在线设备
        devices = getattr(user, 'devices', [])
        is_logged_in = any(getattr(device, 'is_online', lambda: False)() for device in devices)
        
        # 仅为 admin01 添加调试日志
        if getattr(user, 'username', '') == 'admin01':
            lprint(f"[admin01 DTO转换] 开始转换用户信息")
            lprint(f"[admin01 DTO转换] 原始设备列表: {devices}")
            lprint(f"[admin01 DTO转换] 设备数量: {len(devices)}")
            
            # 处理设备信息
            device_list = []
            for device in devices:
                try:
                    device_dict = device.to_dict()
                    lprint(f"[admin01 DTO转换] 设备ID: {device_dict.get('device_id')} 转换前: {device_dict}")
                    # 只对非布尔值进行字符串转换
                    converted_dict = {
                        k: (str(v) if not isinstance(v, bool) and k not in ['login_status', 'websocket_online'] else v) 
                        for k, v in device_dict.items()
                    }
                    lprint(f"[admin01 DTO转换] 设备ID: {device_dict.get('device_id')} 转换后: {converted_dict}")
                    device_list.append(converted_dict)
                except Exception as e:
                    lprint(f"[admin01 DTO转换] 设备转换失败: {str(e)}")
                    traceback.print_exc()
            
            lprint(f"[admin01 DTO转换] 最终设备列表: {device_list}")
        else:
            # 非 admin01 用户直接转换设备列表
            device_list = [{k: str(v) for k, v in device.to_dict().items()} for device in devices]
        
        # 安全地获取时间字段
        created_at = getattr(user, 'created_at', None)
        if isinstance(created_at, datetime):
            created_at = created_at
        else:
            created_at = None
            
        updated_at = getattr(user, 'updated_at', None)
        if isinstance(updated_at, datetime):
            updated_at = updated_at
        else:
            updated_at = None
            
        last_login = getattr(user, 'last_login', None)  # 使用 last_login 作为 last_login
        if isinstance(last_login, datetime):
            last_login = last_login
        else:
            last_login = None
            
        # 安全地获取其他字段
        nickname = str(getattr(user, 'nickname', '')) or None
        extra_data = dict(getattr(user, 'extra_data', {})) or {}
        
        # 为 admin01 添加最终对象的日志
        result = cls(
            id=int(str(getattr(user, 'id', 0))),
            username=str(getattr(user, 'username', '')),
            nickname=nickname,
            avatar_index=int(str(getattr(user, 'avatar_index', 0))),
            role=UserRole(int(str(getattr(user, 'role', UserRole.user)))),
            login_status=is_logged_in,
            created_at=created_at,
            updated_at=updated_at,
            last_login=last_login,
            extra_data=extra_data,
            devices=device_list,
            messages=[]  # 初始化为空列表，消息需要另外设置
        )
        
        if getattr(user, 'username', '') == 'admin01':
            lprint(f"[admin01 DTO转换] 最终转换结果: {result.model_dump()}")
            
        return result

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: format_datetime
        }

class UsersInfoDictResponse(BaseModel):
    """用户信息字典响应数据传输对象
    
    用于返回用户映射信息。
    
    Attributes:
        current_user:
            当前用户
            当前登录用户的信息
        
        user_map:
            用户映射
            用户名到用户信息的映射
    """
    current_user: UserResponse = Field(..., description="当前用户")
    user_map: Dict[str, UserMapInfo] = Field(..., description="用户映射")
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: format_datetime
        }

class Token(BaseModel):
    """JWT Token响应模型"""
    access_token: str = Field(..., description="访问令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    username: str = Field(..., description="用户名")
    role: str = Field(..., description="用户角色")
    nickname: Optional[str] = Field(None, description="昵称")
    avatar_index: Optional[int] = Field(None, description="头像索引")
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: format_datetime
        }

class UserLoginDTO(BaseModel):
    """用户登录请求模型"""
    username: str
    password: str
    device_id: Optional[str] = None
    device_name: Optional[str] = None
    device_type: Optional[str] = None
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: format_datetime
        }

class UserOnlineStatusDTO(BaseModel):
    """用户在线状态数据传输对象
    用于在API层面传输用户的在线状态信息，包括：
    - 用户名
    - 用户状态（来自UserStatusEnum）
    - 设备ID
    """
    username: str
    status: UserStatusEnum
    device_id: Optional[str] = None
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: format_datetime
        }
