# 数据库错误和解决方案

## 会话管理错误

### 1. 'AsyncEngine' object has no attribute 'execute'
**问题描述**：
- 直接在 engine 对象上调用 execute 方法
- 应该使用 session 对象进行数据库操作

**解决方案**：
1. 使用正确的会话管理方式：
   - 依赖注入场景：使用 `get_session()`
   - 直接使用场景：使用 `create_session()`
   - 初始化场景：使用 `engine.begin()`

2. 正确的会话使用方式：
```python
session = await create_session()
try:
    result = await session.execute(stmt)
    await session.commit()
finally:
    await session.close()
```

### 2. 'coroutine' object is not iterable
**问题描述**：
- 尝试直接迭代异步函数的返回值
- 没有使用 `async for` 或 `await`

**解决方案**：
1. 对于生成器函数（如 `get_session()`）：
```python
async with get_session() as session:
    # 使用 session
```

2. 对于普通异步函数：
```python
result = await session.execute(stmt)
```

### 3. 'coroutine' object has no attribute 'first'
**问题描述**：
- 尝试直接在协程对象上调用 `first()`
- 没有等待异步操作完成

**解决方案**：
```python
result = await session.execute(stmt)
item = result.scalar_one_or_none()  # 或 result.first()
```

### 4. 'object async_generator can't be used in 'await' expression'
**问题描述**：
- 尝试直接 await 一个异步生成器函数
- 通常发生在错误使用 `get_session()` 时

**解决方案**：
1. 对于直接使用场景，使用 `create_session()`：
```python
session = None
try:
    session = await create_session()
    # 使用 session
    await session.commit()
except Exception as e:
    if session:
        await session.rollback()
finally:
    if session:
        await session.close()
```

2. 对于依赖注入场景，使用异步上下文管理器：
```python
async with get_session() as session:
    # 使用 session
```

### 5. 'cannot access local variable 'session' where it is not associated with a value'
**问题描述**：
- 在异常处理中访问未初始化的 session 变量
- 通常发生在会话创建失败时

**解决方案**：
1. 在 try 块之前初始化 session：
```python
session = None
try:
    session = await create_session()
    # ...
except Exception as e:
    if session:  # 安全检查
        await session.rollback()
finally:
    if session:  # 安全检查
        await session.close()
```

2. 始终检查 session 是否存在：
- 在回滚时检查
- 在关闭时检查
- 在使用时检查

## 最佳实践

### 1. 会话管理选择
- **依赖注入场景**：使用 `get_session()`
  - FastAPI 路由
  - 需要自动管理生命周期的场景

- **直接使用场景**：使用 `create_session()`
  - 消息处理器
  - WebSocket 处理器
  - 需要手动控制会话的场景

- **数据库初始化**：使用 `engine.begin()`
  - 创建表结构
  - 其他 DDL 操作

### 2. 错误处理
```python
session = await create_session()
try:
    # 数据库操作
    await session.commit()
except Exception as e:
    await session.rollback()
    lprint(f"数据库操作失败: {str(e)}")
    traceback.print_exc()
    raise
finally:
    await session.close()
```

### 3. 资源管理
- 总是在 `try/finally` 块中管理会话
- 确保在所有情况下都能关闭会话
- 使用上下文管理器时要正确处理异步操作

## 常见陷阱

1. **会话泄漏**：
   - 没有正确关闭会话
   - 在异常发生时没有关闭会话

2. **事务管理**：
   - 忘记调用 `commit()`
   - 在错误时忘记 `rollback()`

3. **异步操作**：
   - 忘记使用 `await`
   - 错误使用同步方法

## 调试建议

1. 检查日志中的会话操作：
   - 会话创建
   - 提交/回滚
   - 关闭操作

2. 监控会话数量：
   - 使用数据库连接池监控
   - 检查是否有会话泄漏

3. 事务状态：
   - 确保所有操作都在事务中
   - 检查提交/回滚是否正确执行
