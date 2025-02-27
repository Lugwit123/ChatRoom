// @ts-nocheck
import React from 'react';
import './UserList.css';
import UserAvatar from './UserAvatar';
import { UserBaseAndDevices, UserRole, AccountsMap, Group } from '../types/types';

interface UserListProps {
    current_user: UserBaseAndDevices;
    accounts: AccountsMap;
    groups: Group[];
    onUserSelect: (recipient: string, recipientType: 'user' | 'group') => void;
    selectedRecipient: string | null;
    selectedRecipientType?: 'user' | 'group';
}

const UserList: React.FC<UserListProps> = React.memo(({ current_user, accounts, groups, onUserSelect, selectedRecipient, selectedRecipientType }) => {
    // 使用 useMemo 缓存计算结果
    logger.info('accounts:', accounts);
    const sortedUsers = React.useMemo(() => 
        Object.values(accounts).sort((a, b) => {
            if (a.online === b.online) return 0;
            return a.online ? -1 : 1;
        }), 
        [accounts]
    );

    const { systemUsers, friendUsers } = React.useMemo(() => {
        // 获取所有群组名称
        const groupNames = groups.map(group => group.name);

        const system = sortedUsers.filter(user => 
            user.role === UserRole.system || user.username.includes('system')
        );
        
        const friends = sortedUsers.filter(user => 
            (user.role === UserRole.user || !user.role) && 
            user.username !== current_user?.username && 
            !user.username.includes('system') &&
            !groupNames.includes(user.username)  // 排除群组
        );
        
        return { systemUsers: system, friendUsers: friends };
    }, [sortedUsers, current_user?.username, groups]);

    // 使用 useMemo 缓存排序后的群组
    const sortedGroups = React.useMemo(() => 
        [...groups].sort(),
        [groups]
    );

    // 如果没有当前用户信息且没有系统用户和好友用户，则显示加载中或空状态
    if ((!current_user || !current_user.username) && systemUsers.length === 0 && friendUsers.length === 0) {
        return <div className="user-list-empty">没有可用的用户或正在加载...</div>;
    }

    return (
        <div className="user-list">
            {/* 显示当前登录用户 */}
            {current_user && current_user.username && (
                <div
                    key={`current-${current_user.username}`}
                    className={`user-info current-user ${selectedRecipient === current_user.username ? 'selected' : ''}`}
                    onClick={() => onUserSelect(current_user.username, 'user')}
                >
                    <UserAvatar user={current_user} />
                    <p className="user-name">{current_user.nickname || current_user.username}</p>
                    <span className={`status ${current_user.online ? 'online' : 'offline'}`}></span>
                </div>
            )}

            {/* 显示系统用户列表 */}
            {systemUsers.length > 0 && (
                <div className="system-user-list">
                    <h3 className="system-user-title">系统用户</h3>
                    {systemUsers.map(user => (
                        <div
                            key={`system-${user.username}`}
                            className={`user-info system-user ${selectedRecipient === user.username ? 'selected' : ''}`}
                            onClick={() => onUserSelect(user.username, 'user')}
                        >
                            <UserAvatar user={user} />
                            <p className="user-name">{user.nickname || user.username}</p>
                            <span className={`status ${user.online ? 'online' : 'offline'}`}></span>
                        </div>
                    ))}
                </div>
            )}

            {/* 显示组列表 */}
            {sortedGroups.length > 0 && (
                <div className="group-list">
                    <h3 className="group-title">群组</h3>
                    {sortedGroups.map(group => (
                        <div
                            key={`group-${group.id}-${group.name}`}
                            className={`user-info group ${selectedRecipient === group.name ? 'selected' : ''}`}
                            onClick={() => onUserSelect(group.name, 'group')}
                        >
                            <UserAvatar
                                user={{
                                    username: group.name,
                                    nickname: group.name,
                                    avatar_index: 1,
                                    online: true,
                                    unread_message_count: 0,
                                    role: UserRole.user,
                                    groups: [],
                                    email: undefined,
                                }}
                            />
                            <p className="user-name">{group.name}</p>
                            <span className={`status online`}></span>
                            <span className="group-icon">👥</span>
                        </div>
                    ))}
                </div>
            )}

            {/* 显示好友列表标题 */}
            {friendUsers.length > 0 && (
                <div className="user-title-container">
                    <h3 className="user-title">好友</h3>
                </div>
            )}

            {/* 显示好友列表 */}
            {friendUsers.map(user => {
                if (!user || !user.username) {
                    console.warn(`用户数据不完整或未定义: ${JSON.stringify(user)}`);
                    return null;
                }

                const isSelected = selectedRecipient === user.username;
                return (
                    <div
                        key={`friend-${user.id || user.username}`}
                        className={`user-info ${isSelected ? 'selected' : ''}`}
                        onClick={() => onUserSelect(user.username, 'user')}
                    >
                        <UserAvatar user={user} />
                        <p className="user-name">
                            {user.nickname || user.username}
                            {user.unread_message_count > 0 && (
                                <span className="unread-badge">{user.unread_message_count}</span>
                            )}
                        </p>
                        <span className={`status ${user.online ? 'online' : 'offline'}`}>
                            {user.online ? '' : '离线'}
                        </span>
                    </div>
                );
            })}
        </div>
    );
});

// 添加组件名称，方便调试
UserList.displayName = 'UserList';

export default UserList;
