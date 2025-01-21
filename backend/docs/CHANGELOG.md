## [2025-01-23]

### Added
- 添加了用户映射路由模块 `users_map_router.py`，专门处理用户映射相关的功能
- 在主应用中注册了用户映射路由

### Changed
- 优化了 UserService 中的 get_registered_users 和 get_registered_users 方法，使其更加一致和健壮
- 从 UserBase schema 中移除了 id 字段，因为不是所有响应都需要它
- 优化了用户映射相关的数据模型，确保返回的字段符合前端需求

### Fixed
- 修复了 UserRepository.get_registered_users 方法的事务管理问题
- 修复了用户映射接口的字段验证问题
- 修复了 get_registered_users 方法在错误处理时直接返回空列表的问题，现在会正确抛出异常

## [2025-01-22]

### Added
- 添加了用户映射路由模块 `users_map_router.py`，专门处理用户映射相关的功能
- 在主应用中注册了用户映射路由

### Changed
- 优化了 UserService 中的 get_registered_users 和 get_registered_users 方法，使其更加一致和健壮
- 从 UserBase schema 中移除了 id 字段，因为不是所有响应都需要它
- 优化了用户映射相关的数据模型，确保返回的字段符合前端需求

### Fixed
- 修复了 UserRepository.get_registered_users 方法的事务管理问题
- 修复了用户映射接口的字段验证问题
- 修复了 get_registered_users 方法在错误处理时直接返回空列表的问题，现在会正确抛出异常

## [2025-01-21]

### Changed
- 优化了 UserService 中的 get_registered_users 和 get_registered_users 方法，使其更加一致和健壮
- 从 UserBase schema 中移除了 id 字段，因为不是所有响应都需要它
- 优化了用户映射相关的数据模型，确保返回的字段符合前端需求

### Fixed
- 修复了 UserRepository.get_registered_users 方法的事务管理问题
- 修复了用户映射接口的字段验证问题
- 修复了 get_registered_users 方法在错误处理时直接返回空列表的问题，现在会正确抛出异常

## [2025-01-20]

### Changed
- 从 UserBase schema 中移除了 id 字段，因为不是所有响应都需要它
- 优化了用户映射相关的数据模型，确保返回的字段符合前端需求

### Fixed
- 修复了 UserRepository.get_registered_users 方法的事务管理问题
- 修复了用户映射接口的字段验证问题

## [2025-01-19]

### Added
- 在 UserRepository 和 UserService 中添加了 `get_registered_users` 方法，用于获取所有用户列表
- 在 `UserBaseAndStatus` 模型中添加了 `messages` 字段，用于记录用户与当前登录用户的消息历史
- 创建了 `MessageResponse` 模型用于规范消息响应格式
- 扩展了 `User.to_dict` 方法，支持获取与指定用户的消息记录
- 在 `BaseMessage.to_dict` 方法中添加了 `timestamp` 字段，保持与前端的兼容性
- 在 `BaseMessage.to_dict` 方法中添加了 `public_id` 和 `sender_name` 字段，修复了消息验证错误
- 在 `BaseMessage.to_dict` 方法中添加了 `message_type` 和 `forward_date` 字段，完善消息数据
- 在 `BaseMessage` 类中添加了 `message_type` 属性，用于标识消息类型

### Changed
- 优化 `UserRepository.get_registered_users` 方法，添加设备信息预加载，解决异步环境中的懒加载问题
- 删除 `UserService.get_all_users` 方法，统一使用 `get_registered_users`
- 优化了用户映射功能，现在只在 `user_map` 中的用户才会包含消息记录，且只返回与当前用户相关的消息
- 改进了 `User.to_dict` 方法，添加了设备列表和消息记录的处理逻辑
- 在 `get_users_map` 函数中添加了消息关系的预加载，提高查询效率
- 优化了用户映射功能，现在只在 `user_map` 中的用户才会包含消息记录，且只返回与当前用户相关的消息
- 改进了 `User.to_dict` 方法，添加了设备列表和消息记录的处理逻辑
- 在 `get_users_map` 函数中使用 `get_registered_users` 方法获取用户列表，避免重复代码
- 修复了 `router.py` 中的错误处理，添加了异常链和堆栈跟踪
- 修复了 `selectinload` 导入缺失的问题
- 修复了 `User.to_dict` 方法中时间戳处理的问题，现在会正确处理 None 值
- 统一了数据库访问方式，移除了 `get_user_repo` 依赖，改为直接使用 `get_db` 依赖
- 在 `get_by_username` 方法中添加了设备和消息关系的预加载，修复了懒加载导致的 SQLAlchemy 错误
- 修改了 `BaseMessage` 和 `PrivateMessage` 类的 `to_dict` 方法，使用 `username` 而不是不存在的 `name` 属性
- 优化了 `BaseMessage` 类的字段定义，使用 `Text` 类型替代 `String` 类型存储消息内容
- 移除了未使用的字段：`delete_at` 和 `search_vector`
- 恢复了 `BaseMessage` 类的原有字段定义，确保与数据库结构一致
- 移除了不存在的 `forward_date` 字段，避免数据库查询错误

### Fixed
- 修复了 user/router.py 中 get_user 函数使用错误方法名的问题，将 get_user_by_username 改为正确的 get_by_username
- 修复了 user/router.py 中路由冲突问题，调整了 /map 和 /{username} 路由的顺序
- 修复了 user/router.py 中 get_users_map 函数的返回格式，使其符合测试要求的数据结构
- 修复了 tests/conftest.py 中 User 模型的导入路径，从 app.core.auth.models 改为 app.domain.user.models
- 修复了 tests/conftest.py 中消息模型的导入，使用 PrivateMessage 替代不存在的 Message 类
- 修复了 `User.to_dict` 方法中缺少 `updated_at` 字段的问题

## [0.0.2] - 2024-01-19

### 修复
- 修复了设备更新失败的问题
  - 在 `Device` 模型中添加了 `last_login` 字段
- 修复了用户映射获取失败的问题
  - 在 `UserRepository` 中修复了 `session` 属性的设置器问题

### 改进
- 改进了错误处理和日志记录
- 优化了用户和设备的数据模型
  - 删除了 `Device` 模型中重复的 `last_active_time` 字段，统一使用 `last_login` 字段

## [0.0.3] - 2025-01-24

### 修复
- 修复了设备更新失败的问题
  - 在 `Device` 模型中添加了 `last_login` 字段
- 修复了用户映射获取失败的问题
  - 在 `UserRepository` 中修复了 `session` 属性的设置器问题

### 改进
- 改进了错误处理和日志记录
- 优化了用户和设备的数据模型
  - 删除了 `Device` 模型中重复的 `last_active_time` 字段，统一使用 `last_login` 字段

## [0.0.3] - 2025-01-19

### 修复
- 修复了设备更新失败的问题
  - 在 `Device` 模型中添加了 `last_login` 字段
- 修复了用户映射获取失败的问题
  - 在 `UserRepository` 中修复了 `session` 属性的设置器问题
- 修复了设备模型导入错误
  - 创建了 `device/schemas.py` 文件，定义了 `UserDevice` 模型
  - 在 `user/schemas.py` 中添加了正确的导入
- 修复了用户模型字典转换错误
  - 修改了 `User.to_dict` 方法，确保 `extra_data` 字段始终返回一个字典
  - 优化了时间戳和设备列表的处理逻辑
  - 修复了 `login_status` 属性的调用错误，将其作为属性而不是方法调用
- 修复了消息模型验证错误
  - 从 `MessageBase` 中移除了 `timestamp` 字段的要求
  - 在 `MessageResponse` 中添加了正确的时间戳序列化配置
  - 修改了时间格式，使其与数据库保持一致（使用带时区的ISO格式）
- 统一了所有模型的时间格式
  - 在 `message/schemas.py` 中添加了 `to_timestamp` 工具函数
  - 修改了用户、设备和消息模型的时间格式，统一使用带时区的ISO格式
- 优化了消息ID的设计
  - 区分了内部ID（自增整数）和公开ID（带前缀的字符串）
  - 修改了消息模型和Schema以支持两种ID
  - 在API响应中同时返回两种ID，便于不同场景使用

### 改进
- 改进了错误处理和日志记录
- 优化了用户和设备的数据模型
  - 删除了 `Device` 模型中重复的 `last_active_time` 字段，统一使用 `last_login` 字段
  - 在设备仓储中更新了相关的字段引用

## [Unreleased]

### Added
- 在Device模型中添加`websocket_online`字段,用于跟踪WebSocket连接状态
- 在WebSocket连接和断开时自动更新设备的WebSocket状态
- 设备仓储支持更新WebSocket在线状态
- 添加设备ID持久化的更新记录

### Changed
- 优化设备ID的处理逻辑
  - 从请求头获取设备ID而不是每次生成新的
  - 只有在设备ID不存在或被其他用户占用时才生成新ID
  - 登录响应中返回设备ID供客户端保存
  - 优化设备名称显示,截断过长的user-agent

## [Unreleased]

### 新增
- 添加消息模块单元测试
- 实现WebSocket实时消息支持
- 添加消息归档功能
  - 支持自动归档旧消息
  - 支持清理已归档消息
  - 支持恢复已归档消息

### 优化
- 重构消息模块结构，采用门面模式
- 统一消息处理接口
- 改进错误处理和日志记录

### 修复
- 修复消息发送失败时的错误处理
- 优化WebSocket连接管理
- 完善消息归档逻辑

## [Unreleased]

### 删除
- 删除了 `app/domain/message/service.py`，相关代码已迁移到 `internal/services` 目录
- 删除了 `app/domain/message/repository.py`，相关代码已迁移到 `repositories` 目录
- 删除了 `app/domain/message/routes` 目录，路由定义已整合到 `router.py`
- 删除了 `app/domain/message/handlers.py`，相关代码将与 `internal/handlers/message_handler.py` 合并

## [Unreleased]

### 重构
- 按照新的层级架构重组消息模块的文件结构：
  - 移动 `enums.py` 到 `internal` 目录
  - 移动 `models.py` 到 `internal` 目录
  - 移动 `schemas.py` 到 `facade/dto` 目录
  - 保存旧的 `handlers.py` 到 `internal/handlers/handlers_old.py` 以待合并

### 删除
- 删除了 `app/domain/message/service.py`，相关代码已迁移到 `internal/services` 目录
- 删除了 `app/domain/message/repository.py`，相关代码已迁移到 `repositories` 目录
- 删除了 `app/domain/message/routes` 目录，路由定义已整合到 `router.py`
- 删除了 `app/domain/message/handlers.py`，相关代码将与 `internal/handlers/message_handler.py` 合并

## [Unreleased]

### 重构
- 按照新的层级架构重组消息模块的文件结构：
  - 移动 `enums.py` 到 `internal` 目录
  - 移动 `models.py` 到 `internal` 目录
  - 移动 `schemas.py` 到 `facade/dto` 目录
  - 保存旧的 `handlers.py` 到 `internal/handlers/handlers_old.py` 以待合并

- 重组用户模块的文件结构：
  - 移动 `models.py` 到 `internal/models.py`
  - 移动 `enums.py` 到 `internal/enums.py`
  - 移动 `service.py` 到 `internal/services/user_service.py`
  - 移动 `repository.py` 到 `repositories/user_repository.py`
  - 移动 `schemas.py` 到 `facade/dto/user_dto.py`
  - 移动 `handlers.py` 到 `internal/handlers/user_handler.py`

- 重组群组模块的文件结构：
  - 移动 `models.py` 到 `internal/models.py`
  - 移动 `enums.py` 到 `internal/enums.py`
  - 移动 `service.py` 到 `internal/services/group_service.py`
  - 移动 `repository.py` 到 `repositories/group_repository.py`
  - 移动 `schemas.py` 到 `facade/dto/group_dto.py`

- 重组设备模块的文件结构：
  - 移动 `models.py` 到 `internal/models.py`
  - 移动 `service.py` 到 `internal/services/device_service.py`
  - 移动 `repository.py` 到 `repositories/device_repository.py`
  - 移动 `schemas.py` 到 `facade/dto/device_dto.py`

### 删除
- 删除了 `app/domain/message/service.py`，相关代码已迁移到 `internal/services` 目录
- 删除了 `app/domain/message/repository.py`，相关代码已迁移到 `repositories` 目录
- 删除了 `app/domain/message/routes` 目录，路由定义已整合到 `router.py`
- 删除了 `app/domain/message/handlers.py`，相关代码将与 `internal/handlers/message_handler.py` 合并

## [Unreleased]

### 新增
- 为各个模块创建了外观类（Facade）：
  - `user_facade.py`: 用户模块外观类，提供用户注册、登录、信息管理等功能
  - `group_facade.py`: 群组模块外观类，提供群组创建、成员管理等功能
  - `device_facade.py`: 设备模块外观类，提供设备注册、状态管理等功能

### 重构
- 按照新的层级架构重组消息模块的文件结构：
  - 移动 `enums.py` 到 `internal` 目录
  - 移动 `models.py` 到 `internal` 目录
  - 移动 `schemas.py` 到 `facade/dto` 目录
  - 保存旧的 `handlers.py` 到 `internal/handlers/handlers_old.py` 以待合并

- 重组用户模块的文件结构：
  - 移动 `models.py` 到 `internal/models.py`
  - 移动 `enums.py` 到 `internal/enums.py`
  - 移动 `service.py` 到 `internal/services/user_service.py`
  - 移动 `repository.py` 到 `repositories/user_repository.py`
  - 移动 `schemas.py` 到 `facade/dto/user_dto.py`
  - 移动 `handlers.py` 到 `internal/handlers/user_handler.py`

- 重组群组模块的文件结构：
  - 移动 `models.py` 到 `internal/models.py`
  - 移动 `enums.py` 到 `internal/enums.py`
  - 移动 `service.py` 到 `internal/services/group_service.py`
  - 移动 `repository.py` 到 `repositories/group_repository.py`
  - 移动 `schemas.py` 到 `facade/dto/group_dto.py`

- 重组设备模块的文件结构：
  - 移动 `models.py` 到 `internal/models.py`
  - 移动 `service.py` 到 `internal/services/device_service.py`
  - 移动 `repository.py` 到 `repositories/device_repository.py`
  - 移动 `schemas.py` 到 `facade/dto/device_dto.py`

### 删除
- 删除了 `app/domain/message/service.py`，相关代码已迁移到 `internal/services` 目录
- 删除了 `app/domain/message/repository.py`，相关代码已迁移到 `repositories` 目录
- 删除了 `app/domain/message/routes` 目录，路由定义已整合到 `router.py`
- 删除了 `app/domain/message/handlers.py`，相关代码将与 `internal/handlers/message_handler.py` 合并