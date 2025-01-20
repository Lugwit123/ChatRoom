# 消息系统设计文档

## 1. 设计目标
- 统一私聊和群聊消息的处理流程
- 优化数据库存储效率
- 提供类型安全的API接口
- 简化消息处理逻辑

## 2. 消息模型设计

### 2.1 基础消息模型
所有消息类型共享的基础字段:


### 2.2 私聊消息
在基础消息之上添加接收者字段:
```python
class PrivateMessage(MessageBase):
    recipient: str  # 接收者用户名
```

### 2.3 群组消息
每个群组有独立的消息表,继承基础消息模型:
```python
def create_group_message_table(group_name: str):
    return type(
        f"{group_name}Message",
        (MessageBase,),
        {"__tablename__": f"{group_name}_group_messages"}
    )
```

## 3. 消息处理流程

### 3.1 消息创建
1. 前端使用枚举类型创建消息:


2. 后端处理时转换为ID存储:
```python
# 获取类型ID
msg_type_id = await get_message_type_id(session, message.message_type)
content_type_id = await get_content_type_id(session, message.content_type)
```

### 3.2 消息存储
- 私聊消息存储在 `private_messages` 表
- 群组消息存储在各自的 `{group_name}_group_messages` 表
- 使用ID关联消息类型和内容类型,提高查询效率

### 3.3 消息发送到前端
返回给前端的消息格式:
```python
{
    "id": int,
    "content": str,
    "sender": str,
    "timestamp": datetime,
    "message_type": MessageType,     # 枚举值
    "content_type": MessageContentType, # 枚举值
    "popup_message": bool,
    "status": List[str],
    "recipient": Optional[str],      # 私聊时的接收者
    "group_name": Optional[str]      # 群聊时的群组名
}
```

## 4. 优化说明

### 4.1 数据库优化
- 使用整数ID代替字符串存储消息类型
- 为每个群组创建独立的消息表,避免单表数据过大
- 使用索引优化查询性能

### 4.2 API优化
- 使用枚举提供类型安全
- 统一的消息处理接口
- 清晰的字段命名

### 4.3 代码优化
- 去除冗余字段
- 统一的消息基类
- 清晰的类型转换逻辑

## 5. 后续优化方向
- 消息分页加载
- 消息缓存机制
- 离线消息处理
- 消息同步机制
