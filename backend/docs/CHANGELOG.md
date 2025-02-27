## [2025-01-26]

### Fixed
- 修复了数据库会话管理的问题：
  - 修改了 `user_facade.py` 中的 `get_user_by_username` 方法，使用 `create_session` 替代 `get_session`
  - 添加了正确的事务管理和会话清理
  - 修复了 "async_generator object does not support the asynchronous context manager protocol" 错误

## [2025-01-25]

### Added
- 添加了最新的修改记录

## [2025-01-25]

### Fixed
- 修复了`UserRepository`的导入路径，以适应新的目录结构
  - 在`service_core.py`中更新了导入语句从`app.domain.user.internal.repository`到`app.domain.user.internal.repository.user_repository`
  - 在`user_repository.py`中更新了导入语句从`app.db.database`到`app.db.internal.session`，使用`SessionManager`替代`AsyncSessionLocal`
  - 在`user_repository.py`中更新了导入语句从`app.db.base_repository`到`app.db.repository.base_repository`
  - 在`user_repository.py`中更新了导入语句从`app.domain.common.models.tables`到`app.domain.common.models.tables`
  - 在`models.py`中更新了导入语句从`app.db.base`到`app.db.internal.base`
  - 在`user_repository.py`中更新了导入语句从`app.domain.user.enums`到`app.domain.user.internal.enums`
  - 在`service_core.py`中更新了导入语句从`app.domain.common.models.tables`到`app.domain.common.models.tables`
  - 在`service_core.py`中更新了导入语句从`app.domain.user.enums`到`app.domain.user.internal.enums`
  - 在`user_dto.py`中更新了导入语句从`app.domain.user.facade.dto.enums`到`app.domain.user.internal.enums`
  - 在`message/internal/models.py`中更新了导入语句从`app.db.base`到`app.db.internal.base`
  - 在`message/internal/models.py`中更新了导入语句从`app.domain.message.enums`到`app.domain.message.internal.enums`
  - 在`message/repository/private.py`中更新了导入语句从`app.domain.message.repositories.base`到`app.domain.message.internal.repository.base`
  - 在`message/repository/base.py`中添加了从门面层导入`MessageDTO`
  - 在`message/repository/group.py`中添加了从门面层导入`MessageDTO`和`GroupMemberDTO`
  - 在`message/repository/base.py`中更新了导入语句从`app.domain.common.models.tables.Message`到`app.domain.common.models.tables.BaseMessage`
  - 在`message/repository/base.py`中更新了导入语句从`app.db.base`到`app.db.repository.base_repository`
  - 在`message/repository/group.py`中更新了导入语句从`app.domain.common.models.tables.Message`到`app.domain.common.models.tables.BaseMessage`
  - 在`message/repository/group.py`中更新了导入语句从`app.domain.message.repositorie.base`到`app.domain.message.internal.repository.base`
  - 在`group/internal/models.py`中更新了导入语句从`app.db.base`到`app.db.internal.base`
  - 在`message/repository/base.py`中添加了从门面层导入`MessageDTO`
  - 在`message/repository/group.py`中添加了从门面层导入`MessageDTO`和`GroupMemberDTO`
  - 在`message/facade/dto/message_dto.py`中更新了导入语句从`app.domain.message.models`到`app.domain.common.models.tables`，使用`BaseMessage`替代`Message`

## [2025-01-22]

### Changed
- 统一了数据库会话管理方式：
  - 移除了通过参数传递会话的方式
  - 统一使用 repository 的 session 属性
  - 简化了 UserRepository 和 UserService 中的会话管理代码
  - 避免了会话传递不一致导致的错误

## [2025-01-22]

### Fixed
- 修复了认证问题
  - 修复了`OAuth2PasswordBearer`的`tokenUrl`配置，从`/api/auth/login`改为`api/auth/login`
  - 优化了路由注册，确保认证路由正确配置

- 修复了认证路由重复问题
  - 移除了`auth/router.py`中的重复路由前缀`/api/auth`
  - 移除了`main.py`中认证路由的重复tags标签
  - 优化了路由注册顺序，避免路由冲突

- 修复了设备状态初始化问题
  - 修复了`DeviceRepository`中的`session`属性问题，统一使用`self._session`
  - 修复了`reset_all_devices_status`方法中的字段名称，从`online_status`改为`login_status`和`websocket_online`
  - 优化了数据库初始化顺序，确保`DatabaseFacade`在其他服务之前初始化
  - 修改了`DeviceFacade`的初始化参数，支持传入`DatabaseFacade`实例

## [2025-01-21]

### Changed
- 修复了用户角色枚举的导入问题:
  - 删除了重复创建的 `user/enums.py` 文件
  - 修改了 `group/internal/models.py` 中的导入路径,从 `app.domain.user.enums` 改为 `app.domain.user.internal.enums`
  - 优化了 `Group` 和 `GroupMember` 模型的字段定义,使用 `Text` 替代 `JSON` 类型
  - 恢复了模型的继承关系为 `Base`,因为项目中不存在 `BaseModel`
  - 添加了缺失的 `Index` 导入
  - 从备份目录复制了 `message/schemas.py` 文件到正确位置
  - 从备份目录复制了 `device/schemas.py` 和 `group/schemas.py` 文件到正确位置,并修改了导入路径

## [Unreleased]

### Added
- 添加了 `UserLoginDTO` 类到 `user_dto.py`，用于用户登录请求

### Changed
- 修正了 `user_facade.py` 中的导入语句，将 `UserDTO` 改为 `UserResponse`
- 修正了 `message_service.py` 中的导入语句，将 `MessageRepository` 改为 `BaseMessageRepository`
- 修正了 `message/__init__.py` 中的导入路径，从 `internal.enums` 导入枚举类型
- 修正了 `group_service.py` 中的导入路径：
  - 从 `internal.models` 导入 `Group` 和 `GroupMember`
  - 从 `repository.group_repository` 导入 `GroupRepository` 和 `GroupMemberRepository`
- 修正了 `group_repository.py` 中的导入路径：
  - 从 `internal.models` 导入 `Group` 和 `GroupMember`
  - 从 `db.repository.base_repository` 导入 `BaseRepository`
- 修正了 `user_dto.py` 中的导入路径：
  - 从 `message.facade.dto.schemas` 导入 `MessageResponse` 和 `to_timestamp`
  - 从 `device.facade.dto.schemas` 导入 `DeviceDTO`
- 修正了 `device_dto.py` 中的导入路径：
  - 从 `message.facade.dto.message_dto` 导入 `to_timestamp`

### Removed
- 删除了 `message/facade/dto/schemas.py` 文件，将其内容合并到 `message_dto.py` 中

### Fixed
- 修复了多个导入错误，包括 `UserCreateDTO`、`UserDTO` 和 `MessageRepository` 等
- 修复了日志文件占用问题
- 优化认证错误信息，使其更加清晰易懂
  - 修改了`AuthFacade`中的错误信息，提供更详细的认证失败原因
  - 优化了异常处理器，为认证错误添加更多上下文信息
  - 修复了`get_current_user`的依赖注入问题
- 修复了数据库初始化问题
  - 优化了数据库URL的配置方式，添加默认值
  - 移除了对环境变量DATABASE_URL的强制要求
  - 确保在应用启动时正确加载环境变量
- 修复了用户路由中的数据库实例问题
  - 移除了重复创建的数据库实例
  - 使用主应用中的数据库实例进行依赖注入
  - 优化了错误处理和日志记录
- 修复了OAuth2认证配置问题
  - 修正了`OAuth2PasswordBearer`的`tokenUrl`配置，添加了缺失的前导斜杠
  - 确保认证令牌能正确自动注入到请求中
- 修复了设备注册失败的问题
  - 在`DeviceDTO`中添加了缺失的`user_id`字段
  - 更新了`from_internal`和`to_internal`方法以支持`user_id`字段
  - 解决了`register_device`和`update_device_status`函数中的错误
  - 统一使用`ip_address`字段名,替换`client_ip`
  - 修复了设备创建方法,使用`create_device`替代`create`
  - 修复了设备类型不匹配的问题,使用`DeviceType`枚举替代字符串
- 修复了字段名称不一致的问题
  - 统一使用`group_name`字段名,替换`group_id`
  - 统一使用`message_id`字段名,替换`id`

## [2025-02-03]

### Changed
- 修改消息表结构，支持多个状态并行
  - 将 `BaseMessage` 的 `status` 字段改为 `status` 字段，使用 JSON 类型存储多个状态
  - 添加 `status_enums` 属性和 setter，用于处理状态列表
  - 更新 `to_dict` 方法以支持多状态输出
- 更新消息初始化逻辑，支持从 JSON 文件导入带有多个状态的消息
  - 添加状态列表的解析和验证
  - 设置默认状态为 "sent"
  - 添加必要的默认字段（消息类型、目标类型）
- 优化消息模型结构
  - 移除了 `direction` 字段，因为消息方向可以通过 `sender_id` 和 `recipient_id` 推断
  - 简化了消息的序列化和反序列化逻辑
- 改进消息类型枚举
  - 添加 `private_chat` 类型，用于表示私聊消息
  - 移除了不再使用的 `self_chat` 类型
- 添加群组消息支持
  - 实现群组消息的初始化逻辑
  - 使用分表存储群组消息，提高查询效率
  - 支持从 JSON 文件导入群组消息数据
- 优化群组消息分区计算方式，根据群组 ID 计算分区 ID，确保消息被正确分配到对应分区

## [2025-02-03]

### Changed
- 从 `BaseMessageRepository`、`GroupMessageRepository` 和 `PrivateMessageRepository` 的构造函数中移除会话参数，统一在外部设置会话
- 修改消息仓储的初始化方法，使用父类的会话管理功能

### Fixed
- 修复群组消息初始化时字段名不匹配的问题，使用正确的 `group_name` 字段
- 修复 `GroupMessageRepository` 中缺少必要导入的问题
- 修复 `GroupMessageRepository` 的继承关系，移除重复的 `BaseRepository` 继承
- 修复 `BaseMessageRepository` 的初始化方法，正确调用父类的 `__init__`
- 修复 `PrivateMessageRepository` 的初始化方法，正确调用父类的 `__init__`
- 修复了仓储初始化问题
  - 在 `BaseRepository` 中添加了 `init` 方法，用于初始化仓储
  - 在 `BaseRepository` 的子类中实现了 `init` 方法，用于设置仓储的会话和模型
  - 在 `main.py` 中添加了仓储初始化代码，确保仓储在应用启动时正确初始化

## [2025-01-22]

### Changed
- 重构了数据库会话管理：
  - 在 `DatabaseFacade` 中添加了 `session()` 上下文管理器，统一管理会话的生命周期
  - 修改 `DeviceFacade` 使用 `DatabaseFacade` 的 `session()` 上下文管理器
  - 简化了会话管理代码，移除了重复的会话管理逻辑
  - 修复了会话未正确关闭的问题

## [2025-01-22]

### Added
- 添加了设备状态枚举：
  - 创建了 `app/domain/device/enums` 目录
  - 添加了 `DeviceStatusEnum` 枚举类，定义了设备的在线和离线状态
- 添加了设备状态初始化功能：
  - 在 `DeviceRepository` 中添加了 `init_all_devices_status` 方法
  - 该方法会将所有设备状态重置为离线

### Fixed
- 修复了模块导入错误：
  - 修正了 `DeviceRepository` 中对 `DeviceStatusEnum` 的导入路径
  - 将枚举类从 `internal` 目录移动到了 `enums` 目录
- 修复了缺失方法错误：
  - 添加了缺失的 `init_all_devices_status` 方法到 `DeviceRepository`
  - 修复了启动时初始化设备状态失败的问题

## [2025-01-22]

### Changed
- 重构了设备状态管理：
  - 合并了 `reset_all_devices_status` 和 `init_all_devices_status` 方法
  - 统一使用 `init_all_devices_status` 方法来初始化设备状态
  - 完善了设备状态重置的功能，包括 status、login_status、websocket_online 和 last_login

## [2025-01-22]

### Fixed
- 修复了设备状态更新错误：
  - 移除了不存在的 `status` 字段的更新
  - 使用正确的 `login_status` 和 `websocket_online` 字段
  - 修复了 "Unconsumed column names: status" 错误

## [2025-01-22]

### Changed
- 优化了 UserRepository 的会话管理：
  - 移除了重复的 session 属性定义，使用 BaseRepository 提供的
  - 移除了不必要的 session 参数传递
  - 统一使用仓储自身的 session 属性
  - 修复了用户仓储会话未初始化的问题：
    - 在 UserFacade 初始化时设置 UserRepository 的会话
    - 修复了 "数据库会话未初始化" 错误
    - 修复了登录时的会话相关错误

## [2025-01-22]

### Changed
- 重构了模型映射机制，解决循环导入问题
  - 创建了 `models_registry.py` 来集中管理所有模型的映射关系
  - 修改了所有模型文件使用新的 Base 类
  - 在 main.py 中添加了模型映射配置
  - 统一了所有模型中的关系定义方式

## [2025-01-22]

### Changed
- 重构了模型映射机制，解决循环导入问题
  - 将 `models_registry.py` 移动到 `app/db` 目录下，使其位置更加合理
  - 更新了所有模型文件中的 Base 类导入路径
  - 优化了模型文件的导入结构，使其更加清晰
  - 统一了所有模型中的关系定义方式

## [2025-01-22]

### Changed
- 重构了模型映射机制，解决循环导入问题
  - 将 `models_registry.py` 移动到 `app/domain/common/models` 目录下，更符合领域驱动设计
  - 创建了 `registry.py` 和 `__init__.py` 文件，提供统一的模型导出接口
  - 更新了所有模型文件中的 Base 类导入路径
  - 优化了模型文件的导入结构，使其更加清晰

## [2025-01-22]

### Changed
- 重构了模型映射机制，解决循环导入问题
  - 将 `models_registry.py` 移动到 `app/domain/common/models` 目录下，更符合领域驱动设计
  - 创建了 `registry.py` 和 `__init__.py` 文件，提供统一的模型导出接口
  - 优化了用户和群组模型的关系定义，使用字符串引用避免循环导入
  - 统一了模型属性的命名和类型定义
  - 添加了更多的模型文档字符串
  - 规范化了所有模型的 `to_dict` 方法

## [2025-01-22]

### Changed
- 重构了数据库模型结构，彻底解决循环导入问题
  - 创建了统一的模型文件 `app/domain/common/models/tables.py`
  - 所有数据库表模型都定义在同一个文件中
  - 移除了 `configure_mappers` 函数，不再需要手动配置映射
  - 简化了 `registry.py`，只保留 Base 类定义
  - 通过 `__init__.py` 统一导出所有模型
  - 优化了所有模型的字段定义和关系配置

## [2025-01-22]

### Added
- 重新创建了 `app/domain/common/models/registry.py` 文件
  - 定义了 `BaseModel` 类作为所有模型的基类
  - 添加了 `to_dict()` 和 `__repr__()` 方法
  - 使用 `declarative_base` 创建 `Base` 类

### Changed
- 更新了模型导入结构
  - 在 `tables.py` 中添加了 `generate_public_id` 函数
  - 修改了 `__init__.py` 中的导入方式，使用显式导入
  - 优化了导入顺序和分组

## [2025-01-22]

### Changed
- 重构了 SQLAlchemy Base 类的定义
  - 将 Base 类的定义移到 `app/db/internal/base.py`
  - 添加了 `BaseModel` 类作为所有模型的基类
  - 实现了 `to_dict()` 和 `__repr__()` 方法
  - 更新了 `app/domain/common/models/registry.py` 从 base.py 导入 Base
  - 避免了多处定义 declarative_base 的问题

## [2025-01-22]

### Changed
- 简化了模型导入结构
  - 删除了 `app/domain/common/models/registry.py` 文件
  - 直接从 `app/db/internal/base.py` 导入 Base 类
  - 更新了所有相关模块的导入路径
  - 避免了不必要的中间层

## [2025-01-22]

### Changed
- 修复了消息仓库的导入问题
  - 从 `message_dto.py` 导入 `MessageReaction` 和 `MessageMention` 类型
  - 移除了 `tables.py` 中不必要的模型定义
  - 保持了代码结构的一致性

## [2025-01-22]

### Changed
- 优化了项目结构，移除了冗余的模型注册机制：
  - 删除了 `models_registry.py` 文件，因为所有模型已在 `common/models/tables.py` 中定义
  - SQLAlchemy 会自动处理模型映射，不需要额外配置
  - 这样的改动使代码结构更加清晰，避免了重复定义

## [2025-01-22]

### Fixed
- 修复了设备DTO导入错误：
  - 将 `device_dto.py` 中的 `UserDevice` 类重命名为 `DeviceDTO`
  - 更新了相关的类型注解和文档字符串
  - 确保了与 `device_repository.py` 的导入一致性

## [2025-01-22]

### Fixed
- 修复了设备DTO导入错误：
  - 将 `device_dto.py` 中的 `UserDevice` 类重命名为 `DeviceDTO`
  - 更新了相关的类型注解和文档字符串
  - 确保了与 `device_repository.py` 的导入一致性
- 修复了数据库初始化问题：
  - 在 `main.py` 中添加了 `DatabaseFacade` 的导入
  - 将数据库初始化代码移到 `startup_event` 函数中，避免在模块级别使用 `await`
  - 优化了启动日志输出，使错误信息更清晰
- 修复了设备仓库模块的问题：
  - 在 `device_repository.py` 中添加了缺失的 `traceback` 导入
  - 确保异常处理时可以正确打印堆栈信息
- 修复了设备初始化问题：
  - 在 `main.py` 中将 `reset_all_devices_status` 改为 `init_all_devices_status`
  - 确保方法名与 `DeviceFacade` 中定义的一致

## [2025-02-03]

### Changed
- 从 `BaseMessageRepository`、`GroupMessageRepository` 和 `PrivateMessageRepository` 的构造函数中移除会话参数，统一在外部设置会话
- 修改消息仓储的初始化方法，不再调用父类的 `__init__`，而是直接设置 `model` 和 `_session` 属性

### Fixed
- 修复群组消息初始化时字段名不匹配的问题，使用正确的 `group_name` 字段
- 修复 `GroupMessageRepository` 中缺少必要导入的问题
- 修复 `GroupMessageRepository` 的继承关系，移除重复的 `BaseRepository` 继承
- 修复 `GroupMessageRepository` 的初始化参数，正确传递 session 和 message_model
- 修复 `BaseMessageRepository` 的初始化方法，正确调用父类的 `__init__` 并使用父类的属性
- 修复 `PrivateMessageRepository` 的初始化方法，移除会话参数并正确调用父类的 `__init__`
- 修复所有仓储类中的 `session` 属性访问，统一使用 `_session`
- 修复了仓储初始化问题
  - 在 `BaseRepository` 中添加了 `init` 方法，用于初始化仓储
  - 在 `BaseRepository` 的子类中实现了 `init` 方法，用于设置仓储的会话和模型
  - 在 `main.py` 中添加了仓储初始化代码，确保仓储在应用启动时正确初始化

## [2025-02-03]

### Changed
- 修改消息仓储的继承关系，不再继承 `BaseRepository`，而是直接定义 `model` 和 `_session` 属性
- 修改仓储的初始化方法，统一在构造函数中传入会话参数，避免在外部设置会话

### Fixed
- 修复群组消息初始化时字段名不匹配的问题，使用正确的 `group_name` 字段
- 修复 `GroupMessageRepository` 中缺少必要导入的问题
- 修复 `GroupMessageRepository` 的继承关系，移除重复的 `BaseRepository` 继承
- 修复 `GroupMessageRepository` 的初始化参数，正确传递 session 和 message_model
- 修复 `BaseMessageRepository` 的初始化方法，正确调用父类的 `__init__` 并使用父类的属性
- 修复 `PrivateMessageRepository` 的初始化方法，移除会话参数并正确调用父类的 `__init__`
- 修复所有仓储类中的 `session` 属性访问，统一使用 `_session`

## [2025-02-03]

### Changed
- 删除重复的 `app/db/repository/base_repository.py` 文件
- 统一使用 `app/domain/base/internal/repository/base_repository.py` 作为基础仓储类
- 修改所有仓储类的导入语句，使用正确的 `BaseRepository`
- 修改 `app/db/__init__.py` 中的导入路径，使用正确的 `BaseRepository`

### Fixed
- 修复群组消息初始化时字段名不匹配的问题，使用正确的 `group_name` 字段
- 修复 `GroupMessageRepository` 中缺少必要导入的问题
- 修复 `GroupMessageRepository` 的继承关系，移除重复的 `BaseRepository` 继承
- 修复 `BaseMessageRepository` 的初始化方法，正确调用父类的 `__init__`
- 修复 `PrivateMessageRepository` 的初始化方法，正确调用父类的 `__init__`
- 修复 `app/db/__init__.py` 中的导入错误，使用正确的 `BaseRepository` 路径

## [2025-02-03]

### Changed
- 移动 `base_repository.py` 到正确的位置 `app/domain/base/repository.py`
- 删除重复的 `app/db/repository/base_repository.py` 文件
- 统一使用 `app/domain/base/repository.py` 作为基础仓储类
- 修改所有仓储类的导入语句，使用正确的 `BaseRepository` 路径

### Fixed
- 修复群组消息初始化时字段名不匹配的问题，使用正确的 `group_name` 字段
- 修复 `GroupMessageRepository` 中缺少必要导入的问题
- 修复 `GroupMessageRepository` 的继承关系，移除重复的 `BaseRepository` 继承
- 修复 `BaseMessageRepository` 的初始化方法，正确调用父类的 `__init__`
- 修复 `PrivateMessageRepository` 的初始化方法，正确调用父类的 `__init__`
- 修复所有仓储类中的导入路径，统一使用 `app/domain/base/repository.py`

## [2025-02-07]

### Removed
- 删除了 `app/domain/user/dependencies.py` 文件,因为:
  1. 该文件提供的依赖注入功能在迁移到门面模式后不再需要
  2. 文件中的功能已被 `UserFacade` 替代
  3. 没有活跃代码依赖这个文件
- 删除了 `app/domain/user/internal/services/service_core.py` 文件,因为:
  1. 合并用户服务层到门面层,简化代码结构
  2. 所有服务层功能已迁移到 `UserFacade` 中
  3. 遵循门面模式,减少代码层级
- 删除了 `app/domain/group/internal/services/group_service.py` 文件,因为:
  1. 合并群组服务层到门面层,简化代码结构
  2. 所有服务层功能已迁移到 `GroupFacade` 中
  3. 遵循门面模式,减少代码层级
- 删除了以下消息服务层文件:
  - `app/domain/message/internal/services/message_service_interface.py`
  - `app/domain/message/internal/services/message_service.py`
  - `app/domain/message/internal/services/message_archive_service.py`
  原因:
  1. 合并消息服务层到门面层,简化代码结构
  2. 所有服务层功能已迁移到 `MessageFacade` 中
  3. 遵循门面模式,减少代码层级

## [Unreleased]

### Changed
- 将消息管理器文件从repository移动到managers文件夹
  - 移动`private_message_manager.py`到`app/domain/message/internal/managers/`
  - 移动`group_message_manager.py`到`app/domain/message/internal/managers/`
  - 更新了相关的导入路径
  - 创建了新的`managers`模块
- 添加 `get_message_facade()` 函数到 message_facade.py，实现消息门面的单例模式访问
- 添加全局变量 `_message_facade` 用于存储消息门面单例
- 更新 `get_message_facade()` 函数，添加 WebSocketFacade 和 socketio.AsyncServer 依赖

### Fixed
- 修复了 router.py 中无法导入 get_user_facade 的问题
- 确保了用户门面的单例模式实现
- 修复了 user_router.py 中对已删除的 user_message_dto 的引用，改为使用 message_dto
- 修复了错误的类型导入，将 UsersMessageMappingResponse 改为从 user_dto 导入 UsersMessageMapResponse
- 修复了 router.py 中无法导入 get_message_facade 的问题
- 修复了 user_router.py 中对已删除的 user_message_dto 的引用，改为使用 message_dto
- 修复了错误的类型导入，将 UsersMessageMappingResponse 改为从 user_dto 导入 UsersMessageMapResponse
- 修复了 router.py 中无法导入 get_message_facade 的问题，改为从 app.domain.message.facade 导入

### Removed
- 删除了 `UsersMessageMapResponse` 类，改用 `UsersInfoDictResponse` 作为用户映射响应
- 修改了 router.py 中的路由返回类型和响应模型

## [2025-02-07]

### Added
- 添加了最新的修改记录
- 添加 `get_user_facade()` 函数到 user_facade.py，实现用户门面的单例模式访问
- 添加全局变量 `_user_facade` 用于存储用户门面单例
- 添加 `get_message_facade()` 函数到 message_facade.py，实现消息门面的单例模式访问
- 添加全局变量 `_message_facade` 用于存储消息门面单例

### Fixed
- 修复了 router.py 中无法导入 get_user_facade 的问题
- 确保了用户门面的单例模式实现
- 修复了 user_router.py 中对已删除的 user_message_dto 的引用，改为使用 message_dto
- 修复了错误的类型导入，将 UsersMessageMappingResponse 改为从 user_dto 导入 UsersMessageMapResponse
- 修复了 router.py 中无法导入 get_message_facade 的问题
- 修复了 user_router.py 中对已删除的 user_message_dto 的引用，改为使用 message_dto
- 修复了错误的类型导入，将 UsersMessageMappingResponse 改为从 user_dto 导入 UsersMessageMapResponse
- 修复了 router.py 中无法导入 get_message_facade 的问题，改为从 app.domain.message.facade 导入

### Removed
- 删除了 `UsersMessageMapResponse` 类，改用 `UsersInfoDictResponse` 作为用户映射响应
- 修改了 router.py 中的路由返回类型和响应模型

## [2025-02-07]

### Changed
- 重组了认证相关的 DTO 结构，将 UserAuthDTO 从 user_dto.py 移到 auth_dto.py
- 修复了 auth_facade.py 中重复导入 UserAuthDTO 的问题
- 优化了认证模块和用户模块之间的依赖关系

## [2025-02-07]

### Changed
- 修复了认证模块中 get_current_user 的类型和错误处理
- 改进了用户不存在时的错误处理，确保返回明确的错误信息
- 修正了 get_current_user 的返回类型从 UserInfo 到 User

## [2025-02-07]

### Fixed
- 修复了 auth_facade.py 中缺少 User 模型导入的问题

## [2025-02-07]

### Added
- 在 UserRepository 中添加了 get_user_by_username 方法，支持根据用户名查询用户信息

## [2025-02-07]

### Changed
- 重构 UserRepository.get_user_by_username 方法，使用基础仓储类的方式实现，保持代码一致性

## [2025-02-07]

### Fixed
- 修复了 get_user_by_username 方法中的懒加载问题，通过 selectinload 预加载 devices 关系

## [2025-02-07]

### Fixed
- 修复了 UserBaseAndDevices.from_internal 方法中设备列表的类型不匹配问题，现在正确获取设备 ID

## [Unreleased]

### Changed
- 修复了 PrivateMessageRepository 中 case() 函数的语法错误
- 重组了 private.py 的导入顺序,遵循标准库>第三方库>本地模块的规范
- 添加了完整的异常处理和日志记录

### Fixed
- 修复了 MessageDTO 验证错误
  - 在 get_user_messages_map 中将 PrivateMessage 对象转换为字典
  - 移除了 SQLAlchemy 内部状态字段
  - 使用字典作为 model_validate 的输入