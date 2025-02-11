// frontend/src/types/types.tsx

// 使用正则表达式进行 Email 格式的简单验证
function isEmail(email: string): boolean {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

// 自定义 Email 类型
export type EmailStr = string & { __email__: never };

export function asEmail(email: string): EmailStr | null {
    if (isEmail(email)) {
        return email as EmailStr;
    }
    return null;
}

export interface CurrentLoginUser {
    username:string 
}

// 用户角色枚举
export enum UserRole {
    admin = 'admin',
    user = 'user',
    system = 'system',
    test = 'test'
}

// 消息类型枚举
export enum MessageType {
    BROADCAST = 'broadcast',
    PRIVATE_CHAT = 'private_chat',
    GROUP_CHAT = 'group_chat',
    CHAT_HISTORY = 'chat_history',
    SELF_CHAT = 'self_chat',
    SYSTEM = 'system',
    VALIDATION = 'validation',
    USER_LIST_UPDATE = 'user_list_update',
    ERROR = 'error',
    GET_USERS = 'get_users',
    REMOTE_CONTROL = 'remote_control',
    OPEN_PATH = 'open-path',
    USER_STATUS_UPDATE = 'user_status_update'
}

// 消息内容类型枚举
export enum MessageContentType {
    RICH_TEXT = 'rich_text',
    URL = 'url',
    AUDIO = 'audio',
    IMAGE = 'image',
    VIDEO = 'video',
    FILE = 'file',
    PLAIN_TEXT = 'plain_text',
    USER_LIST = 'user_list',
    HTML = 'html',
    TEXT = 'text'
}

// frontend/src/types/types.tsx

// 群组接口
export interface Group {
    id: number;
    name: string;
    members?: UserBaseAndStatus[];
}

// 群组映射接口
export interface GroupsMap {
    [key: string]: Group;  // key 是群组名称
}



// 用户基础信息接口
export interface UserBase {
    id: number;
    username: string;
    nickname?: string;
    email?: string;
    role?: UserRole;
    avatar_index?: number;
    online?: boolean;
    groups?: Group[];
}

// 扩展用户基础信息，添加消息相关字段
export interface UserBaseAndStatus extends UserBase {
    messages?: MessageBase[];
    unread_message_count: number;
    status: 'online' | 'offline';
    isStarred?: boolean;  // 添加特别关注字段
}

export enum MessageDirection{
    RESPONSE = 'response',
    REQUEST  = 'request'
}

export enum MessageStatus {
    UNREAD = "unread",    // 未读
    READ = "read",        // 已读
    PENDING = "pending",  // 处理中
    SUCCESS = "success",  // 处理成功
    FAILED = "failed"     // 处理失败
}

export const popup_message=false

// MessageBase 接口
export  interface MessageBase {
    id?: number | string; // 消息ID
    sender?: string; // 发送者用户名
    recipient?: string | string[]; // 接收者ID，支持单个用户名/群组名或接收者列表
    content?: any; // 消息内容，GET_USERS 类型消息时为 UserListResponse 类型数据
    timestamp?: string; // 消息时间戳 (ISO 格式字符串)
    recipient_type?: 'private' | 'group' | 'all' | 'self_chat'; // 消息类型，例如 'private' 或 'group'
    status?: MessageStatus[]; // 消息状态，例如 'unread' 或 'read'
    message_content_type?: MessageContentType; // 消息类型
    message_type: MessageType; // 消息类别，如 'broadcast'、'private_chat'、'system' 等
    direction? : MessageDirection;
    popup_message?: boolean;
    
    // 针对 VALIDATION 类型的字段
    validation_type?: string | null; // 验证的具体类型
    validation_extra_data?: Record<string, unknown> | null; // 与验证相关的附加数据
}

// 为不同类型的消息定义具体的接口
export interface TextMessage extends MessageBase {
    message_content_type: MessageContentType.PLAIN_TEXT | MessageContentType.HTML;
    content: string;
}

export interface UserListMessage extends MessageBase {
    message_content_type: MessageContentType.USER_LIST;
    content: {
        user_list: UserBaseAndStatus[];
        groups: Group[];
    };
}


// 账户映射接口
export interface AccountsMap {
    [username: string]: UserBaseAndStatus ;
}

// 户列表响应接口
// 定义 UsersInfoDictResponse 接口
export interface UsersInfoDictResponse {
    current_user: UserBaseAndStatus; // 当前用户的信息
    user_map: Record<string, UserBaseAndStatus>; // 其他用户的详细信息列表，键是用户的 ID（字符串）
}

// 户列表响应接口
export interface UserListResponse {
    users: UserBaseAndStatus[];
}

// WebSocket 消息类型
export interface WebSocketMessage extends MessageBase {
    sender: string;
    receiver: string;
    content: string;
    timestamp: string;
    type: 'text' | 'image' | 'file';
}

export interface UserListUpdateMessage extends WebSocketMessage {
    message_type: MessageType.USER_LIST_UPDATE;
    user_list: UserBaseAndStatus[];
    groups: string[];
}

export interface SystemMessage extends WebSocketMessage {
    message_type: MessageType.SYSTEM;
}

export interface ChatHistoryMessage extends WebSocketMessage {
    message_type: MessageType.CHAT_HISTORY;
    username: string;
    messages: MessageBase[];
}

export interface ChatHistoryRequestMessage {
    message_type: MessageType.CHAT_HISTORY;
    username: string;
}

export interface GroupChatMessage extends WebSocketMessage {
    message_type: MessageType.GROUP_CHAT;
}

export interface PrivateChatMessage extends WebSocketMessage {
    message_type: MessageType.PRIVATE_CHAT;
}

export interface SelfPrivateChatMessage extends WebSocketMessage {
    message_type: MessageType.SELF_CHAT;
}

export interface ErrorMessage extends WebSocketMessage {
    message_type: MessageType.ERROR;
    error: string;
}

// 用户登录请求接口
export interface UserLoginRequest {
    username: string;
    password: string;
    mode?: 'login';
}

// 用户注册请求接口
export interface UserRegistrationRequest {
    username: string;
    password: string;
    nickname?: string;
    email?: EmailStr;
    age?: number;
    mode: 'register';
    role: UserRole;
}

// 修改 AccountType 接口
export interface AccountType extends UserBase {
    messages: MessageBase[];  // 改为使用 MessageBase[]
    unread_message_count: number;
}

// 添加认证相关接口
export interface AuthResponse {
    access_token: string;
    token_type: string;
    username: string;
    role: string;
    detail?: string;
}

export interface JWTPayload {
    sub: string;
    exp: number;
}

export type UserStatus = 'online' | 'offline';

export interface UseUserListProps {
    token: string;
    current_user: UserBaseAndStatus | null;
    updateUsers: (users: AccountsMap) => void;
    onError: (error: string) => void;
    setError: (error: string) => void;
}

// 可能需要修改这个接口
export interface ChatPanelProps {
    account: UserBaseAndStatus | null;
    current_user: string;
    wsConnected: boolean;
    handleSendMessage: (message: MessageBase) => void;
    setAccounts?: (users: UserBaseAndStatus[]) => void; // 可以设置为可选
    setLoadingDetails?: () => void;
}
