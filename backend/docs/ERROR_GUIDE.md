# 错误指南

## 1. 错误预防

### 1.1 数据库操作错误
#### 'AsyncEngine' object has no attribute 'execute'
✅ 正确写法:
```python
async with async_session() as session:
    result = await session.exec(stmt)
```

❌ 错误写法:
```python
result = await engine.execute(stmt)  # 错误：engine没有execute方法
```

#### 'coroutine' object is not iterable
✅ 正确写法:
```python
result = await session.exec(stmt)
items = result.all()  # 或 .first()
```

❌ 错误写法:
```python
items = session.exec(stmt)  # 错误：没有await异步操作
for item in items:  # 错误：直接遍历协程对象
    pass
```

#### 'coroutine' object has no attribute 'first'
✅ 正确写法:
```python
result = await session.exec(stmt)
item = result.first()
```

❌ 错误写法:
```python
result = session.exec(stmt)  # 错误：没有await
item = result.first()  # 错误：直接调用协程对象的方法
```

## 2. 代码检查清单

### 2.1 每次修改前检查
- [ ] 查看错误指南中的常见错误
- [ ] 确认代码符合最佳实践
- [ ] 检查类似代码的历史错误

### 2.2 代码编写检查
- [ ] 所有数据库操作都在 async with 上下文中
- [ ] 所有异步操作都使用了 await
- [ ] 查询结果正确获取 (.all(), .first() 等)
- [ ] 使用 session.exec() 而不是 execute()
- [ ] 正确处理事务（需要时使用 commit/rollback）

### 2.3 异步操作检查
- [ ] 异步函数定义使用 async def
- [ ] 异步操作都使用了 await
- [ ] 异步循环使用 async for
- [ ] 异步上下文使用 async with
- [ ] 避免在同步代码中调用异步函数

## 3. 错误记录

### 3.1 数据库错误
1. SQLAlchemy连接错误
   - 原因：数据库连接字符串错误或数据库未启动
   - 解决：检查连接字符串和数据库状态

2. 事务错误
   - 原因：未正确处理事务或并发问题
   - 解决：使用 async with session.begin()

### 3.2 异步错误
1. 协程未等待
   - 原因：忘记使用 await
   - 解决：确保所有异步操作都使用 await

2. 异步上下文错误
   - 原因：未使用 async with
   - 解决：使用正确的异步上下文管理器

## 4. 最佳实践

### 4.1 数据库操作
```python
async def safe_db_operation():
    try:
        async with async_session() as session:
            async with session.begin():
                stmt = select(Model).where(Model.id == id)
                result = await session.exec(stmt)
                item = result.first()
                return item
    except SQLAlchemyError as e:
        lprint(f"数据库操作失败: {e}")
        raise DatabaseError(str(e))
```

### 4.2 错误处理
```python
try:
    result = await operation()
except Exception as e:
    lprint(f"操作失败: {e}")
    raise CustomError(f"操作失败: {str(e)}")
```

## 5. 自动检查工具

### 5.1 代码检查
```python
def check_common_errors(code: str) -> List[str]:
    errors = []
    if "engine.execute" in code:
        errors.append("使用了 engine.execute 而不是 session.exec")
    if "await" not in code and "async" in code:
        errors.append("异步函数缺少 await")
    return errors
```

### 5.2 运行时检查
```python
def validate_async_result(result):
    if iscoroutine(result):
        raise ValueError("未处理的协程对象，请使用 await")
    return result
```

## 6. 持续改进

1. 定期更新错误指南
2. 记录新发现的错误模式
3. 改进代码模板
4. 优化检查工具
5. 分享经验教训

## 7. 注意事项

1. 每次修改代码前先查看本指南
2. 遇到新错误及时记录
3. 使用代码检查工具
4. 保持良好的编码习惯
5. 定期回顾和更新指南
