# ChatRoom 后端文档

## 1. 项目概述

ChatRoom 是一个基于 FastAPI 的聊天室后端服务，支持：
- 私聊和群聊
- 文件传输
- 设备管理
- 用户认证

## 2. 技术栈

- FastAPI: Web 框架

- Socket.IO: 实时通信
- PostgreSQL: 数据库
- Python 3.8+

## 3. 项目结构

```
backend/
├── app/
│   ├── core/                 # 核心功能
│   │   ├── auth.py          # 认证
│   │   ├── config.py        # 配置
│   │   ├── connection_manager.py  # WebSocket管理
│   │   ├── exception_handlers.py  # 异常处理
│   │   ├── logging_config.py      # 日志配置
│   │   └── message_handlers.py    # 消息处理
│   ├── db/                  # 数据库
│   │   ├── repository.py    # 数据库仓库
│   │   └── schemas.py       # 数据模型
│   └── routers/             # API路由
│       ├── device_routes.py # 设备路由
│       ├── file_routes.py   # 文件路由
│       └── message_routes.py # 消息路由
├── data/                    # 数据文件
├── docs/                    # 文档
└── logs/                    # 日志文件
```

## 4. 核心功能

### 4.1 消息系统
- 请求-响应模型
- 实时消息推送
- 消息状态追踪

### 4.2 用户管理
- JWT 认证
- 角色权限
- 设备绑定

### 4.3 文件传输
- 文件上传/下载
- 文件类型验证
- 存储管理

### 4.4 群组管理
- 群组创建/删除
- 成员管理
- 群组消息

## 5. 快速开始

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 初始化数据库：
```bash
python init_database.py
```

3. 启动服务器：
```bash
cmd /c run_backend_server.bat
```

## 6. 开发规范

### 6.1 代码规范
- 使用 Black 格式化代码
- 遵循 PEP 8 规范
- 类型注解全覆盖

### 6.2 日志规范
```python
import Lugwit_Module as LM
lprint = LM.lprint

# 使用示例
lprint("操作信息", level=logging.INFO)
```

### 6.3 异常处理
```python
try:
    result = await operation()
except Exception as e:
    lprint(f"操作失败: {e}")
    raise HTTPException(status_code=500, detail=str(e))
```

### 6.4 数据库操作
```python
async with async_session() as session:
    try:
        result = await session.execute(stmt)
        await session.commit()
    except SQLAlchemyError as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
```

## 7. 常见问题

### 7.1 数据库错误
1. `AsyncEngine` 错误
   ```python
   # 错误写法
   result = await engine.execute(stmt)
   
   # 正确写法
   async with async_session() as session:
       result = await session.execute(stmt)
   ```

2. 协程错误
   ```python
   # 错误写法
   users = session.execute(stmt)
   
   # 正确写法
   result = await session.execute(stmt)
   users = result.scalars().all()
   ```

### 7.2 导入错误
- backend 根目录下不使用相对导入
- 使用绝对导入路径

### 7.3 日志错误
- 使用 `lprint` 而不是 `logger`

## 8. 待办事项

- [ ] 优化数据库查询性能
- [ ] 完善单元测试
- [ ] 添加更多 API 文档
- [ ] 实现消息队列
- [ ] 优化文件存储

## 9. 联系方式

如有问题，请联系：
- 开发团队：[团队邮箱]
- 项目负责人：[负责人邮箱]
