// frontend\src\components\UserList.tsx
import React, { useState, useEffect, useMemo } from 'react';
import './UserList.css';
import { pinyin } from 'pinyin-pro';
import UserAvatar from './UserAvatar';
import { UserBaseAndStatus, UserRole, Group, UsersInfoDictResponse } from '../types/types';
import useCurrentSelectedUserStore from '../stores/useCurrentSelectedUserStore';
import { AiFillStar, AiOutlineStar } from 'react-icons/ai';

const UserList: React.FC<{
    users: UsersInfoDictResponse;
    groups: Group[];
    onUserSelect?: (recipient: string, recipientType: 'user' | 'group') => void;
}> = React.memo(({ 
    users, 
    groups = [],
    onUserSelect, 
}) => {
    const selectUser = useCurrentSelectedUserStore((state) => state.selectUser);
    const currentSelectedUser = useCurrentSelectedUserStore((state) => state.currentSelectedUser);
    const [selectedRecipient, setSelectedRecipient] = React.useState<string>('system01');
    const [selectedType, setSelectedType] = React.useState<'user' | 'group'>('user');
    const [starredUsers, setStarredUsers] = React.useState<Set<string>>(new Set());
    const [searchText, setSearchText] = useState('');
    const [showHistory, setShowHistory] = useState(false);
    const [searchHistory, setSearchHistory] = useState<string[]>(() => {
        const saved = localStorage.getItem('userSearchHistory');
        return saved ? JSON.parse(saved) : [];
    });

    // 保存搜索历史到 localStorage
    useEffect(() => {
        localStorage.setItem('userSearchHistory', JSON.stringify(searchHistory));
    }, [searchHistory]);

    // 添加搜索记录
    const addToHistory = (text: string) => {
        if (!text.trim()) return;
        setSearchHistory(prev => {
            const newHistory = [text, ...prev.filter(item => item !== text)].slice(0, 10);
            return newHistory;
        });
    };

    // 删除搜索记录
    const removeFromHistory = (text: string, e: React.MouseEvent) => {
        e.stopPropagation();
        setSearchHistory(prev => prev.filter(item => item !== text));
    };

    // 处理搜索输入
    const handleSearchInput = (e: React.ChangeEvent<HTMLInputElement>) => {
        setSearchText(e.target.value);
    };

    // 处理搜索框失焦
    const handleSearchBlur = () => {
        // 延迟隐藏历史记录，以便点击历史记录项
        setTimeout(() => setShowHistory(false), 200);
        if (searchText.trim()) {
            addToHistory(searchText.trim());
        }
    };

    // 选择历史记录
    const selectHistory = (text: string) => {
        setSearchText(text);
        setShowHistory(false);
    };

    const handleToggleStar = (username: string) => {
        setStarredUsers(prev => {
            const newSet = new Set(prev);
            if (newSet.has(username)) {
                newSet.delete(username);
            } else {
                newSet.add(username);
            }
            return newSet;
        });
    };

    const handleSelectUser = (user: UserBaseAndStatus): void => {
        selectUser(user);
        setSelectedRecipient(user.username);
        setSelectedType('user');
        onUserSelect?.(user.username, 'user');
    }

    const handleSelectUserbyUserName = (username: string): void => {
        // 从 user_map 中获取用户对象
        const user = users.user_map[username];
    
        if (user) {
            console.log(`set current user "${username}"`);
            handleSelectUser(user); // 用户存在，调用 handleSelectUser
        } else {
            console.warn(`User with username "${username}" not found.`);
        }
    };
    (window as any).handleSelectUserbyUserName = handleSelectUserbyUserName;

    const handleSelectGroup = (groupName: string): void => {
        setSelectedRecipient(groupName);
        setSelectedType('group');
        onUserSelect?.(groupName, 'group');
    }

    // 对用户进行排序和分类
    const current_user = users?.current_user;
    let user_map = users?.user_map || {};
    
    const { sortedUsers, systemUsers, friendUsers } = React.useMemo(() => {
        if (!user_map) return { sortedUsers: [], systemUsers: [], friendUsers: [] };
        
        const sorted = Object.values(user_map).map(user => ({
            ...user,
            isStarred: starredUsers.has(user.username)
        })).sort((a, b) => {
            if (a.isStarred !== b.isStarred) return a.isStarred ? -1 : 1;
            if (a.online !== b.online) return a.online ? -1 : 1;
            return 0;
        });

        const groupNames = new Set((groups || []).map(group => group.name));

        const system = sorted.filter(user => 
            user.role === UserRole.system && user.username != current_user?.username
        );
        
        const friends = sorted.filter(user => 
            (user.role === UserRole.user || !user.role) && 
            user.username !== current_user?.username && 
            !user.username.includes('system') &&
            !groupNames.has(user.username)
        );
        
        return { 
            sortedUsers: sorted, 
            systemUsers: system, 
            friendUsers: friends 
        };
    }, [users, current_user?.username, groups, starredUsers]);

    // 用户过滤逻辑
    const filteredUsers = useMemo(() => {
        if (!searchText) {
            // 返回除当前用户外的所有用户
            return sortedUsers.filter(user => user.username !== current_user?.username);
        }
        
        return sortedUsers
            .filter(user => user.username !== current_user?.username) // 先过滤掉当前用户
            .filter(user => {
                const username = user.username.toLowerCase();
                const search = searchText.toLowerCase();
                
                // 原文匹配
                if (username.includes(search)) return true;
                
                // 获取拼音
                const pinyinFull = pinyin(username, { toneType: 'none' }).toLowerCase();
                if (pinyinFull.includes(search)) return true;
                
                // 获取拼音首字母
                const pinyinFirst = pinyin(username, { pattern: 'first', toneType: 'none' }).toLowerCase();
                return pinyinFirst.includes(search);
            });
    }, [sortedUsers, searchText, current_user?.username]);

    // 排序群组
    const sortedGroups = React.useMemo(() => 
        groups ? [...groups].sort((a, b) => a.name.localeCompare(b.name)) : [],
        [groups]
    );

    // 检查是否有数据可显示
    if (!current_user?.username && systemUsers.length === 0 && friendUsers.length === 0) {
        return <div className="user-list-empty">没有可用的用户或正在加载...</div>;
    }

    return (
        <div className="user-list">
            {/* 搜索框 */}
            <div className="user-list-search">
                <div className="search-container">
                    <input
                        type="text"
                        placeholder="搜索用户（支持拼音首字母）"
                        value={searchText}
                        onChange={handleSearchInput}
                        onFocus={() => setShowHistory(true)}
                        onBlur={handleSearchBlur}
                    />
                    {showHistory && searchHistory.length > 0 && (
                        <div className="search-history">
                            {searchHistory.map((text, index) => (
                                <div
                                    key={index}
                                    className="search-history-item"
                                    onClick={() => selectHistory(text)}
                                >
                                    <span>{text}</span>
                                    <button
                                        className="delete-btn"
                                        onClick={(e) => removeFromHistory(text, e)}
                                    >
                                        删除
                                    </button>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>
            
            {/* 当前用户 */}
            {current_user?.username && (
                <UserItem
                    user={current_user}
                    isSelected={selectedRecipient === current_user.username}
                    onClick={() => handleSelectUser(current_user)}
                />
            )}

            {/* 系统用户 */}
            {systemUsers.length > 0 && (
                <div className="system-user-list">
                    <h3 className="system-user-title">系统用户</h3>
                    {systemUsers.map(user => (
                        <UserItem
                            key={`system-${user.username}`}
                            user={user}
                            isSelected={selectedRecipient === user.username}
                            onClick={() => handleSelectUser(user)}
                            isSystemUser
                        />
                    ))}
                </div>
            )}

            {/* 群组列表 */}
            {sortedGroups.length > 0 && (
                <div className="group-list">
                    <h3 className="group-title">群组</h3>
                    {sortedGroups.map(group => (
                        <GroupItem
                            key={`group-${group.id}-${group.name}`}
                            group={group}
                            isSelected={selectedRecipient === group.name}
                            onClick={() => handleSelectGroup(group.name)}
                        />
                    ))}
                </div>
            )}

            {/* 好友列表 */}
            {friendUsers.length > 0 && (
                <>
                    <div className="user-title-container">
                        <h3 className="user-title">好友</h3>
                    </div>
                    {filteredUsers.map(user => (
                        user && user.username ? (
                            <UserItem
                                key={`friend-${user.id || user.username}`}
                                user={user}
                                isSelected={selectedRecipient === user.username}
                                onClick={() => handleSelectUser(user)}
                                onToggleStar={handleToggleStar}
                            />
                        ) : null
                    ))}
                </>
            )}
        </div>
    );
});

// 用户项组件
const UserItem: React.FC<{
    user: UserBaseAndStatus;
    isSelected: boolean;
    onClick: () => void;
    isSystemUser?: boolean;
    onToggleStar?: (username: string) => void;
}> = React.memo(({ user, isSelected, onClick, isSystemUser, onToggleStar }) => (
    <div
        className={`user-info ${isSystemUser ? 'system-user' : ''} ${isSelected ? 'selected' : ''}`}
        onClick={onClick}
    >
        <UserAvatar user={user} />
        <p className={`user-name ${user.online ? 'online' : 'offline'}`}>
            {user.nickname || user.username}
            {user.unread_message_count > 0 && (
                <span className="unread-badge">{user.unread_message_count}</span>
            )}
        </p>
        {!isSystemUser && (
            <div 
                className={`star-icon ${user.isStarred ? 'visible' : ''}`}
                onClick={(e) => {
                    e.stopPropagation();
                    onToggleStar?.(user.username);
                }}
            >
                {user.isStarred ? <AiFillStar /> : <AiOutlineStar />}
            </div>
        )}
    </div>
));

// 群组项组件
const GroupItem: React.FC<{
    group: Group;
    isSelected: boolean;
    onClick: () => void;
}> = React.memo(({ group, isSelected, onClick }) => (
    <div
        className={`user-info group ${isSelected ? 'selected' : ''}`}
        onClick={onClick}
    >
        <UserAvatar
            user={{
                id: 0,
                username: group.name,
                nickname: group.name,
                avatar_index: 1,
                online: true,
                unread_message_count: 0,
                role: UserRole.user,
                groups: [],
                email: undefined,
                status: 'online',
            }}
        />
        <p className="user-name">{group.name}</p>
        <span className="status online"></span>
        <span className="group-icon">👥</span>
    </div>
));

UserItem.displayName = 'UserItem';
GroupItem.displayName = 'GroupItem';
UserList.displayName = 'UserList';

export default UserList;
