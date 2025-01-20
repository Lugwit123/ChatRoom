# 数据库修改记录

## 2025-01-14 数据库初始化改进

### 1. 安全性改进
- 将用户表中的 `password` 字段改为 `hashed_password`
- 使用 `pwd_context.hash()` 对密码进行哈希处理
- 确保所有密码都以哈希形式存储

### 2. 数据模型改进
- 添加了私聊消息表的创建逻辑
- 修正了时间戳处理，统一使用带时区的时间格式
- 使用 Asia/Shanghai 时区

### 3. 代码结构优化
- 创建独立的 `create_users` 函数处理用户创建
- 添加了详细的错误处理和日志记录
- 优化了数据库初始化流程

### 4. 初始数据
- 添加了基本用户：admin（管理员）和 test（普通用户）
- 添加了示例私聊消息
- 确保所有初始数据都有正确的时间戳

### 5. 导入优化
- 添加必要的 SQLAlchemy 导入
- 修正了 datetime 相关的导入

## 2025-01-15 群消息表修复

### 1. 枚举类型修正
- 修正了 `recipient_type` 字段的枚举值
- 从 `MessageTargetType.group_chat` 改为 `MessageTargetType.group`
- 确保与 `schemas.py` 中的枚举定义一致

### 2. 群消息表结构
每个群组都有独立的消息表，包括：
- `group_messages_asset_group`
- `group_messages_effect_group`
- `group_messages_solve_group`
- `group_messages_light_group`

### 3. 表结构定义
每个群消息表包含以下字段：
```sql
CREATE TABLE IF NOT EXISTS group_messages_[group_name] (
    id SERIAL PRIMARY KEY,
    content VARCHAR,
    sender_id INTEGER REFERENCES users(id),
    recipient_type messagetargettype,
    recipient VARCHAR,
    group_name VARCHAR REFERENCES groups(name),
    timestamp TIMESTAMP WITH TIME ZONE,
    message_type_id INTEGER REFERENCES message_types(id),
    message_content_type_id INTEGER REFERENCES message_content_types(id),
    status VARCHAR[],
    popup_message INTEGER,
    extra_data VARCHAR
)
```

### 4. 初始消息数据
每个群消息表初始化时包含两条消息：
1. 欢迎消息：
   ```python
   {
       'content': f'欢迎来到{group_name}群！',
       'sender_id': 1,  # admin用户
       'recipient_type': MessageTargetType.group,
       'recipient': group_name,
       'group_name': group_name,
       'timestamp': current_time,
       'message_type_id': message_type_id,
       'message_content_type_id': message_content_type_id,
       'status': ['sent'],
       'popup_message': False,
       'extra_data': '{}'
   }
   ```

2. 管理员消息：
   ```python
   {
       'content': '大家好，我是管理员',
       'sender_id': 1,
       'recipient_type': MessageTargetType.group,
       'recipient': group_name,
       'group_name': group_name,
       'timestamp': current_time,
       'message_type_id': message_type_id,
       'message_content_type_id': message_content_type_id,
       'status': ['sent'],
       'popup_message': False,
       'extra_data': '{}'
   }
   ```

### 5. 数据库初始化流程
1. 清空现有数据库
2. 创建必要的枚举类型
3. 创建基础表（用户、组等）
4. 为每个群组创建独立的消息表
5. 插入初始消息数据

### 6. 注意事项
1. 确保 `MessageTargetType` 枚举使用正确的值（`group` 而不是 `group_chat`）
2. 所有时间戳使用 Asia/Shanghai 时区
3. 初始消息的 sender_id 为1（admin用户）
4. 每个群组的消息存储在独立的表中，表名格式为 `group_messages_[group_name]`

## 数据库表关系
1. 群消息表通过 `sender_id` 关联 `users` 表
2. 群消息表通过 `group_name` 关联 `groups` 表
3. 群消息表通过 `message_type_id` 关联 `message_types` 表
4. 群消息表通过 `message_content_type_id` 关联 `message_content_types` 表

## 注意事项
1. 运行初始化脚本前确保数据库服务正常运行
2. 初始化会清空现有数据，请谨慎操作
3. 可以在日志文件中查看初始化过程的详细信息
