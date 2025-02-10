# 备份代码总结 (20250111_154510)

## 核心文件



### user_database.py
- 数据库操作核心文件
- 包含用户、消息、群组等数据库操作
- 使用SQLModel作为ORM

### schemas.py
- 数据模型定义
- 包含用户、消息、群组等数据结构
- 使用SQLModel定义数据库模型和API模型

## 认证和权限

### authenticate.py
- 用户认证相关功能
- JWT token生成和验证
- 用户权限检查

### dependencies.py
- FastAPI依赖项定义
- 当前用户获取功能
- 其他通用依赖项

## 消息处理

### message_handlers.py
- WebSocket消息处理逻辑
- 实时消息推送功能
- 消息状态管理

### message_routes.py
- 消息相关的HTTP路由
- 消息CRUD操作
- 消息查询接口

### connection_manager.py
- WebSocket连接管理
- 用户在线状态管理
- 消息广播功能

## 工具和辅助功能

### utils.py
- 通用工具函数
- 随机字符串生成
- 其他辅助功能

### encoding_utils.py
- 编码相关工具
- 处理中文编码问题
- 控制台输出编码设置

### logging_config.py
- 日志配置
- 日志格式定义
- 日志文件管理

### exception_handlers.py
- 全局异常处理器
- 自定义错误响应
- 错误日志记录

### move_files.py
- 文件移动和管理工具
- 用于代码部署和备份

## 主要变更
1. 修复了导入路径问题
2. 添加了UserInDatabase模型
3. 优化了日志配置
4. 统一使用lprint进行日志记录
5. 改进了错误处理机制

## 注意事项
1. 所有后端模块使用绝对导入
2. 日志文件位于./logs/server.log
3. 使用SQLModel替代SQLAlchemy
4. 每个群组使用独立的消息表
5. 时间戳使用带时区的格式
