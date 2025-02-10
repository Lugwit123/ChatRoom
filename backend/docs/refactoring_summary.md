# 后端重构总结

## 重构目标

1. 改进代码组织结构
2. 统一数据模型定义
3. 提高代码可维护性
4. 优化数据库操作

## 目录结构

```
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       └── endpoints/
│   │           ├── messages.py
│   │           ├── users.py
│   │           └── groups.py
│   ├── core/
│   │   ├── config.py
│   │   ├── exceptions.py
│   │   ├── logging.py
│   │   └── websocket/
│   │       ├── manager.py
│   │       └── handlers.py
│   ├── db/
│   │   ├── database.py
│   │   ├── schemas.py
│   │   └── repositories/
│   │       ├── base.py
│   │       ├── user.py
│   │       ├── group.py
│   │       └── message.py
│   ├── utils/
│   │   └── encoding_utils.py
│   └── main.py
├── data/
├── logs/
├── tests/
└── uploads/
```

## 主要改动

### 1. 统一模型定义



- 改进了类型提示和验证
- 统一使用带时区的datetime

### 2. 仓储模式实现

创建了专门的仓储类处理数据库操作：

- `BaseRepository`: 通用CRUD操作
- `UserRepository`: 用户相关操作
- `GroupRepository`: 群组相关操作
- `MessageRepository`: 消息相关操作

### 3. WebSocket重构

- 将WebSocket相关代码移至专门的模块
- 改进了连接管理
- 优化了消息处理流程

### 4. 日志系统

- 统一使用 `lprint` 进行日志记录
- 配置了日志格式和级别
- 添加了更多的日志记录点

### 5. 错误处理

常见错误及解决方案：

1. `'AsyncEngine' object has no attribute 'execute'`
   - 原因：SQLAlchemy异步操作使用不当
   - 解决：使用正确的异步会话管理

2. `'coroutine' object is not iterable`
   - 原因：未正确处理异步迭代器
   - 解决：使用 `async for` 或 `await`

3. `'coroutine' object has no attribute 'first'`
   - 原因：未等待异步结果
   - 解决：添加 `await` 关键字

## 代码示例

### 模型定义

`

### 仓储使用

```python
async def get_user(username: str):
    async with AsyncSession() as session:
        user_repo = UserRepository()
        return await user_repo.get_by_username(session, username)
```

## 后续工作

1. 完善单元测试
2. 添加API文档
3. 优化数据库查询性能
4. 实现更多的WebSocket功能
5. 添加更多的日志监控

## 注意事项

1. 所有时间戳都使用带时区的datetime
2. 数据库初始化顺序：清空 -> 创建用户 -> 创建群组 -> 插入消息
3. 不要在其他目录重复创建初始化文件
4. 使用 `backend\app\utils\encoding_utils.py` 解决控制台乱码
5. 运行后端代码时先切换到后端目录

## 使用的技术栈

- FastAPI

- PostgreSQL
- WebSocket
- Pydantic
- Python 3.8+

## 维护指南

1. 代码修改后检查是否出现新问题
2. 使用 `lprint` 而不是 `logger`
3. 保持代码结构清晰
4. 定期检查日志文件
5. 遵循类型提示和文档规范
