# 代码结构分析报告

生成时间: 2025-01-11 23:07:35

## 20250111_154510\authenticate.py

### 函数

- `decode_token` (第 24 行)
- `authenticate_token` (第 46 行)
- `create_access_token` (第 85 行)
- `cleanup_cache` (第 106 行)
- `start_cleanup_task` (第 123 行)

## 20250111_154510\backend_main.py

### 函数

- `authenticate_user` (第 81 行)
- `custom_swagger_ui_html` (第 149 行)
- `register` (第 162 行)
- `login` (第 226 行)
- `read_root` (第 271 行)
- `delete_user_endpoint` (第 276 行)
- `get_user_list` (第 317 行)
- `get_groups` (第 346 行)
- `get_all_groups_endpoint` (第 363 行)
- `get_groups` (第 377 行)
- `get_members_of_group` (第 400 行)
- `get_announcement` (第 442 行)
- `send_message` (第 451 行)
- `get_messages` (第 540 行)
- `uploads` (第 607 行)
- `get_check_result` (第 631 行)
- `batch_delete_users` (第 649 行)
- `message_clicked` (第 698 行)
- `verify_token` (第 704 行)
- `startup_event` (第 722 行)
- `main` (第 749 行)
- `cleanup_devices` (第 730 行)

## 20250111_154510\connection_manager.py

### 函数

- `__init__` (第 38 行)
- `connect` (第 48 行)
- `disconnect` (第 76 行)
- `get_username` (第 95 行)
- `get_groups` (第 102 行)
- `broadcast_user_list` (第 108 行)
- `broadcast` (第 158 行)
- `send_with_retry` (第 167 行)
- `send_system_message` (第 198 行)
- `send_group_message` (第 214 行)
- `get_user` (第 228 行)
- `broadcast_to_group` (第 232 行)
- `broadcast` (第 251 行)
- `send_message` (第 270 行)
- `send_system_message` (第 279 行)

### 方法

- `ConnectionManager.__init__` (第 38 行)
- `ConnectionManager.connect` (第 48 行)
- `ConnectionManager.disconnect` (第 76 行)
- `ConnectionManager.get_username` (第 95 行)
- `ConnectionManager.get_groups` (第 102 行)
- `ConnectionManager.broadcast_user_list` (第 108 行)
- `ConnectionManager.broadcast` (第 158 行)
- `ConnectionManager.send_with_retry` (第 167 行)
- `ConnectionManager.send_system_message` (第 198 行)
- `ConnectionManager.send_group_message` (第 214 行)
- `ConnectionManager.get_user` (第 228 行)
- `ConnectionManager.broadcast_to_group` (第 232 行)
- `ConnectionManager.broadcast` (第 251 行)
- `ConnectionManager.send_message` (第 270 行)
- `ConnectionManager.send_system_message` (第 279 行)

## 20250111_154510\dependencies.py

### 函数

- `get_current_user_response` (第 11 行)
- `get_current_user_db` (第 24 行)

## 20250111_154510\encoding_utils.py

### 函数

- `setup_encoding` (第 13 行)
- `get_encoding_info` (第 34 行)
- `print_encoding_info` (第 47 行)

## 20250111_154510\exception_handlers.py

### 函数

- `http_exception_handler` (第 6 行)
- `general_exception_handler` (第 10 行)

## 20250111_154510\logging_config.py

### 函数

- `setup_logging` (第 5 行)

## 20250111_154510\message_handlers.py

### 函数

- `__init__` (第 24 行)
- `setup_socketio_handlers` (第 29 行)
- `handle_connect` (第 36 行)
- `handle_disconnect` (第 94 行)
- `handle_message` (第 104 行)
- `handle_validation` (第 147 行)
- `handle_private_message` (第 160 行)
- `handle_group_message` (第 169 行)
- `handle_get_users` (第 202 行)
- `send_initial_data` (第 254 行)
- `send_chat_histories` (第 300 行)
- `broadcast_user_status_change` (第 344 行)

### 方法

- `MessageHandlers.__init__` (第 24 行)
- `MessageHandlers.setup_socketio_handlers` (第 29 行)
- `MessageHandlers.handle_connect` (第 36 行)
- `MessageHandlers.handle_disconnect` (第 94 行)
- `MessageHandlers.handle_message` (第 104 行)
- `MessageHandlers.handle_validation` (第 147 行)
- `MessageHandlers.handle_private_message` (第 160 行)
- `MessageHandlers.handle_group_message` (第 169 行)
- `MessageHandlers.handle_get_users` (第 202 行)
- `MessageHandlers.send_initial_data` (第 254 行)
- `MessageHandlers.send_chat_histories` (第 300 行)
- `MessageHandlers.broadcast_user_status_change` (第 344 行)

## 20250111_154510\message_routes.py

### 函数

- `parse_indices` (第 14 行)
- `delete_messages` (第 45 行)

## 20250111_154510\move_files.py

### 函数

- `ensure_directory` (第 8 行)
- `create_init_file` (第 14 行)
- `create_directories` (第 21 行)
- `copy_file_with_backup` (第 43 行)
- `move_files` (第 63 行)
- `update_imports` (第 86 行)

## 20250111_154510\schemas.py

### 函数

- `get_group_names` (第 119 行)
- `serialize_timestamp` (第 285 行)
- `add_status` (第 289 行)
- `parse_message_ids` (第 329 行)
- `serialize_timestamp` (第 445 行)
- `serialize_timestamp` (第 469 行)

### 方法

- `UserInDatabase.get_group_names` (第 119 行)
- `MessageBase.serialize_timestamp` (第 285 行)
- `MessageBase.add_status` (第 289 行)
- `DeleteMessagesRequest.parse_message_ids` (第 329 行)
- `GroupChatMessage.serialize_timestamp` (第 445 行)
- `SelfPrivateChatMessage.serialize_timestamp` (第 469 行)

## 20250111_154510\user_database.py

### 函数

- `init_message_types` (第 204 行)
- `get_message_type_id` (第 234 行)
- `get_content_type_id` (第 245 行)
- `create_tables` (第 260 行)
- `validate_username` (第 270 行)
- `validate_nickname` (第 275 行)
- `insert_group` (第 280 行)
- `get_group_by_name` (第 296 行)
- `insert_user` (第 303 行)
- `fetch_user` (第 358 行)
- `background_message_ids_updater` (第 413 行)
- `update_user_message_ids` (第 442 行)
- `insert_message` (第 467 行)
- `fetch_all_users` (第 534 行)
- `fetch_registered_users` (第 552 行)
- `verify_user` (第 576 行)
- `is_user_admin` (第 588 行)
- `get_user_by_id` (第 597 行)
- `fetch_messages` (第 619 行)
- `fetch_group_messages` (第 674 行)
- `get_chat_history` (第 722 行)
- `set_user_online_status` (第 750 行)
- `get_all_groups_info` (第 765 行)
- `delete_user` (第 777 行)
- `load_initial_users` (第 792 行)
- `load_initial_messages` (第 832 行)
- `update_messages_status` (第 906 行)
- `update_group_messages_status` (第 926 行)
- `fetch_unread_count` (第 949 行)
- `fetch_user_or_group` (第 969 行)
- `get_all_groups_response` (第 1002 行)
- `get_group_members` (第 1027 行)
- `fetch_users_by_condition` (第 1050 行)
- `start_background_tasks` (第 1078 行)
- `update_user_last_message` (第 1086 行)
- `process_message_updates` (第 1094 行)
- `update_message_ids` (第 1135 行)
- `update_all_message_ids` (第 1173 行)
- `start_background_tasks` (第 1213 行)
- `get_column_value` (第 1221 行)
- `convert_message_status` (第 1230 行)
- `create_message_base` (第 1237 行)
- `delete_messages` (第 1253 行)
- `get_recent_message_ids` (第 167 行)
- `get_all_message_ids` (第 179 行)
- `safe_id` (第 191 行)
- `safe_username` (第 195 行)

### 方法

- `UserResponse.get_recent_message_ids` (第 167 行)
- `UserResponse.get_all_message_ids` (第 179 行)
- `UserResponse.safe_id` (第 191 行)
- `UserResponse.safe_username` (第 195 行)

## 20250111_154510\utils.py

### 函数

- `get_avatar_index` (第 6 行)
- `generate_random_string` (第 9 行)
- `get_current_time` (第 12 行)

## 20250111_154510\routers\check_file\abc_router.py

### 函数

- `validate_input` (第 29 行)
- `root` (第 33 行)
- `show_results` (第 40 行)
- `generate_path` (第 77 行)
- `list_check_files` (第 101 行)

## 20250111_154510\routers\check_file\config.py

### 函数

- `add_check_file_static` (第 21 行)

