# 开发指南

## 1. 开发环境设置

### 1.1 Python 环境
- Python 3.8+
- 虚拟环境管理：venv 或 conda

### 1.2 依赖安装
```bash
pip install -r requirements.txt
```

### 1.3 IDE 配置
- VSCode 或 PyCharm
- 安装 Python 插件
- 配置代码格式化工具 (Black)
- 配置 linter (flake8)

## 2. 代码规范

### 2.1 命名规范
- 类名：PascalCase
- 函数名：snake_case
- 变量名：snake_case
- 常量：UPPER_CASE
- 私有成员：_leading_underscore

### 2.2 文件组织
- 每个模块一个目录
- 相关功能放在同一目录
- 使用 __init__.py 导出接口

### 2.3 导入规范
```python
# 标准库
import os
import sys
from typing import List, Optional

# 第三方库


# 项目内部
from app.core.config import settings
from app.db.repository import UserRepository
```

### 2.4 类型注解
```python
from typing import Optional, List
from datetime import datetime

def get_user_messages(
    username: str,
    start_date: Optional[datetime] = None,
    limit: int = 100
) -> List[Message]:
    ...
```

## 3. 数据库开发

### 3.1 模型定义


### 3.2 仓库模式
```python
class UserRepository:
    async def get_by_username(
        self,
        session: AsyncSession,
        username: str
    ) -> Optional[User]:
        stmt = select(User).where(User.username == username)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
```

### 3.3 事务处理
```python
async def create_user_with_devices(user_data: dict, devices: List[dict]):
    async with async_session() as session:
        async with session.begin():
            try:
                user = User(**user_data)
                session.add(user)
                for device in devices:
                    device['user_id'] = user.id
                    session.add(Device(**device))
                await session.commit()
            except Exception as e:
                await session.rollback()
                raise
```

## 4. API 开发

### 4.1 路由定义
```python
@router.get("/{username}", response_model=UserResponse)
async def get_user(username: str):
    async with async_session() as session:
        user = await UserRepository().get_by_username(session, username)
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        return user
```

### 4.2 请求验证
```python
class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=6)
```

### 4.3 响应处理
```python
class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: UserRole
    created_at: datetime
```

## 5. WebSocket 开发

### 5.1 连接管理
```python
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
```

### 5.2 消息处理
```python
@sio.on('message')
async def handle_message(sid, data):
    try:
        await process_message(data)
        await sio.emit('message_processed', {'status': 'success'}, room=sid)
    except Exception as e:
        lprint(f"消息处理错误: {e}")
        await sio.emit('error', {'detail': str(e)}, room=sid)
```

## 6. 测试开发

### 6.1 单元测试
```python
async def test_create_user():
    async with async_session() as session:
        user = await UserRepository().create(
            session,
            username="test",
            email="test@example.com"
        )
        assert user.username == "test"
```

### 6.2 集成测试
```python
async def test_user_api():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/users/", json={
            "username": "test",
            "email": "test@example.com",
            "password": "password123"
        })
        assert response.status_code == 200
```

## 7. 部署

### 7.1 环境配置
- 设置环境变量
- 配置数据库连接
- 配置日志路径

### 7.2 服务器设置
- 使用 uvicorn 或 gunicorn
- 配置 worker 数量
- 设置超时时间

### 7.3 监控
- 使用 Prometheus 收集指标
- 配置 Grafana 面板
- 设置告警规则
