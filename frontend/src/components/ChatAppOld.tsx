// frontend/src/components/ChatApp.tsx
// @ts-nocheck
import React, { useState, useEffect, useRef } from 'react';
import { useQuery } from '@tanstack/react-query';
import UserList from './UserList';
import ChatPanel from './ChatPanel';
import AccountForm from './AccountForm';
import CurrentLoginUserDisplay from './CurrentLoginUserDisplay';
import StarryBackground from './StarryBackground';
import { UserBaseAndStatus, MessageResponse, AccountsMap, Group, UserRole } from '../types/types';
import { useAuth } from '../hooks/useAuth';
import { useUserList } from '../hooks/useUserList';
import { useChatHistory } from '../hooks/useChatHistory';
import { useWebSocketConnection } from '../hooks/useWebSocketConnection';
import { sendMessageToServer } from '../utils/messageUtils';
import { useGroup } from '../contexts/GroupContext';
import { getUserInfoDict, getGroups } from '../services/api';
import './ChatApp.css';

function ChatApp() {
    const apiUrl = import.meta.env.VITE_API_URL;
    const { groups: contextGroups, getGroupMembers } = useGroup();
    const {
        token,
        current_user,
        accounts,
        setAccounts,
        error: authError,
        setError,
        mode,
        setMode,
        handleAddAccount,
        handleLogout,
    } = useAuth(apiUrl);

    const [users, setUsers] = useState<UserBaseAndStatus[]>([]);
    const [selectedRecipient, setSelectedRecipient] = useState<string>('system01');
    const [selectedRecipientType, setSelectedRecipientType] = useState<'user' | 'group'>('user');
    const [isAccountsReady, setIsAccountsReady] = useState(false);

    // 添加加载步骤状态
    const [loadingStep, setLoadingStep] = useState<string>('初始化...');

    // 添加初始化状态追踪
    const [initializationStep, setInitializationStep] = useState<string>('开始初始化...');
    const [isInitializing, setIsInitializing] = useState(true);

    // 监听 token 和 current_user 的变化
    useEffect(() => {
        if (!token) {
            setInitializationStep('等待登录...');
            setIsInitializing(false);  // 如果没有 token，说明需要登录
            setIsAccountsReady(false);
            return;
        }

        if (!current_user) {
            setInitializationStep('验证用户信息...');
            return;
        }

        setInitializationStep('正在加载用户数据...');
    }, [token, current_user]);

    // 监听 accounts 的变化
    useEffect(() => {
        if (Object.keys(accounts).length > 0) {
            setLoadingStep('账户数据已加载');
            logger.info('accounts 已准备好:', accounts);
            setIsAccountsReady(true);
            setIsInitializing(false);
        }
    }, [accounts]);

    // React Query hooks
    const { 
        data: userListData,
        error: userListError,
        isLoading: isUserListLoading
    } = useQuery({
        queryKey: ['userList'],
        queryFn: () => {
            setLoadingStep('正在获取用户列表...');
            return getUserInfoDict();
        },
        enabled: !!token
    });

    const {
        data: groupsData,
        error: groupsError,
        isLoading: isGroupsLoading
    } = useQuery<string[]>({
        queryKey: ['groups'],
        queryFn: async () => {
            setLoadingStep('正在获取群组信息...');
            const groups = await getGroups();
            return groups;
        },
        enabled: !!token
    });

    // 使用 useRef 保持最新的 accounts 状态
    const accountsRef = useRef<AccountsMap>({});
    useEffect(() => {
        accountsRef.current = accounts;
    }, [accounts]);

    // 使用自定义钩子获取用户列表
    useUserList({
        apiUrl,
        token,
        current_user,
        setAccounts,
        setUsers,
        setGroups: () => {}, // 由于现在使用 React Query 管理groups,这里可以传空函数
        setError,
    });

    // 使用自定义钩子获取聊天历史
    const { fetchChatHistory } = useChatHistory(apiUrl, token, setAccounts);

    // 使用自定义钩子处理 WebSocket 连接
    const { isConnected, message } = useWebSocketConnection(
        apiUrl,
        token,
        current_user,
        selectedRecipient,
        setAccounts
    );

    const prevSelectedRecipient = useRef<string | null>(null);
    
    // 聊天历史获取逻辑
    useEffect(() => {
        if (selectedRecipient !== prevSelectedRecipient.current) {
            prevSelectedRecipient.current = selectedRecipient;
            
            if (selectedRecipient) {
                fetchChatHistory(selectedRecipient);
            }
        }
    }, [selectedRecipient, accounts, fetchChatHistory]);

    // 设置默认选择为系统用户
    useEffect(() => {
        if (!selectedRecipient && accounts['system01']) {
            setSelectedRecipient('system01');
            setSelectedRecipientType('user');
        }
    }, [accounts, selectedRecipient]);

    // 发送消息处理函数
    const handleSendMessage = (
        message: string,
        senderUsername: string,
        avatarIndex: number
    ) => {
        sendMessageToServer(
            message,
            selectedRecipient,
            senderUsername,
            avatarIndex,
            message,
            setAccounts,
            selectedRecipientType,
            groupsData || []
        );
    };

    // 错误处理
    const error = authError || userListError || groupsError;
    if (error) {
        return <div className="error-message">错误: {error instanceof Error ? error.message : String(error)}</div>;
    }

    // 加载状态处理
    if (isInitializing) {
        return (
            <div className="loading">
                <div className="loading-spinner"></div>
                <div className="loading-text">{initializationStep}</div>
                <div className="loading-step">{loadingStep}</div>
                <div className="loading-progress">请稍候...</div>
            </div>
        );
    }

    // 如果没有 token，显示登录表单
    if (!token) {
        return <AccountForm onSubmit={handleAddAccount} mode={mode} setMode={setMode} />;
    }

    // 如果正在加载数据
    if (!isAccountsReady || isUserListLoading || isGroupsLoading) {
        return (
            <div className="loading">
                <div className="loading-spinner"></div>
                <div className="loading-text">{loadingStep}</div>
                <div className="loading-progress">请稍候...</div>
            </div>
        );
    }

    return (
        <div className="chat-container">
            <StarryBackground />
            <CurrentLoginUserDisplay
                current_user={accounts[current_user]? {
                    ...accounts[current_user],
                    messages: accounts[current_user]?.messages || [],
                    groups: accounts[current_user]?.groups || [],
                    role: accounts[current_user]?.role || UserRole.user,
                    online: accounts[current_user]?.online || false,
                    unread_message_count: accounts[current_user]?.unread_message_count || 0,
                } : null}
                handleLogout={handleLogout}
            />

            {!current_user ? (
                <AccountForm onSubmit={handleAddAccount} mode={mode} setMode={setMode} />
            ) : (
                <div className="main-content">
                    <UserList
                        current_user={accounts[current_user]}
                        accounts={accounts}
                        groups={groupsData?.map(group => ({ id: 0, name: group })) || []}
                        onUserSelect={(recipient, type) => {
                            setSelectedRecipient(recipient);
                            setSelectedRecipientType(type);
                        }}
                        selectedRecipient={selectedRecipient}
                        selectedRecipientType={selectedRecipientType}
                    />
                    {selectedRecipient ? (
                        (selectedRecipientType === 'user' && accounts[selectedRecipient]) ||
                        (selectedRecipientType === 'group' && groupsData?.includes(selectedRecipient)) ? (
                            <ChatPanel
                                account={selectedRecipientType === 'user' ? {
                                    ...accounts[selectedRecipient],
                                    messages: accounts[selectedRecipient]?.messages || []
                                } : null}
                                current_user={current_user}
                                users={users}
                                wsConnected={isConnected}
                                handleSendMessage={(message: string) =>
                                    handleSendMessage(
                                        message,
                                        current_user || '系统用户',
                                        accounts[current_user || 'system']?.avatar_index || 0
                                    )
                                }
                            />
                        ) : (
                            <div className="chat-panel">
                                <p>选择的账户信息未找到。</p>
                            </div>
                        )
                    ) : (
                        <div className="chat-panel">
                            <p>请选择一个用户或群组开始聊天。</p>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}

export default ChatApp;
