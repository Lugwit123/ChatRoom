// frontend/src/hooks/useWebSocketMessageHandler.tsx
// @ts-nocheck
import { useCallback, useState, useEffect, useMemo } from 'react';
import { useWebSocketConnection, WebSocketConnectionReturn } from './useWebSocketConnection';
import { Socket } from 'socket.io-client';
import { apiUrl } from '../services/api';
import {
    MessageBase,
    UserListUpdateMessage,
    SystemMessage,
    ChatHistoryRequestMessage,
    GroupChatMessage,
    PrivateChatMessage,
    SelfPrivateChatMessage,
    AccountsMap,
    UserRole,
    ChatHistoryMessage,
    MessageType,
    ErrorMessage,
    MessageContentType,
    UserListResponse
} from '../types/types';
import { get_avatar_index } from '../utils/getAvatarIndex';
import { useTitleBlink } from './useTitleBlink';
import { useChatHistory } from './useChatHistory';

export const useWebSocketMessageHandler = (
    current_user: string | null,
    selectedUser: string | null,
    setAccounts: React.Dispatch<React.SetStateAction<AccountsMap>>,
    setLoadingDetails: React.Dispatch<React.SetStateAction<{
        step: string;
        details: string;
        progress: number;
    }>>
) => {
    const [shouldBlink, setShouldBlink] = useState<boolean>(false);
    useTitleBlink({
        trigger: shouldBlink,
        blinkText: '新消息!',
        blinkInterval: 1000,
    });

    const { updateChatHistory, addMessage } = useChatHistory(
        localStorage.getItem('token'),
        setAccounts,
        selectedUser
    );

    // 添加日志来追踪 current_user 的值
    useEffect(() => {
        logger.info('useWebSocketMessageHandler - current_user:', current_user);
    }, [current_user]);

    // 通用更新 AccountsMap 的方法
    const updateAccounts = useCallback(
        (updater: (prevAccounts: AccountsMap) => AccountsMap, relevantMessage: boolean) => {
            setAccounts((prevAccounts) => updater(prevAccounts));
            if (relevantMessage) {
                setShouldBlink(true);
                if (Notification.permission === 'granted') {
                    const notification = new Notification('新消息', {
                        body: '您有一条新消息!',
                    });
                    notification.onclick = () => {
                        window.focus();
                        setShouldBlink(false);
                        notification.close();
                    };
                }
            }
        },
        [setAccounts]
    );

    // 先定义消息处理器映射
    const messageHandlers = useMemo<Record<MessageType, (data: MessageBase) => void>>(() => ({
        [MessageType.PRIVATE_CHAT]: (data) => {
            logger.info("WebSocketMessageHandler - 收到私聊消息:", {
                data,
                current_user,
                selectedUser
            });
            if (data.recipient_type === 'private') {
                logger.info("WebSocketMessageHandler - 准备添加消息到历史记录");
                addMessage(data);
                if (data.sender !== current_user) {
                    setShouldBlink(true);
                }
            }
        },
        [MessageType.GET_USERS]: (data) => {
            logger.info("收到完整用户列表:", data);
            if (data.content && typeof data.content === 'object') {
                const { user_list, groups } = data.content as UserListResponse;
                
                if (user_list && Array.isArray(user_list)) {
                    logger.info("开始初始化用户列表, 用户数:", user_list.length);
                    setLoadingDetails(prev => ({
                        ...prev,
                        step: '正在处理用户数据',
                        details: `正在加载 ${user_list.length} 个用户...`,
                        progress: 60
                    }));

                    updateAccounts(() => {
                        const newAccounts: AccountsMap = {};
                        user_list.forEach((user, index) => {
                            if (user && user.username) {
                                logger.info("添加用户:", user.username, {
                                    role: user.role,
                                    isUser: user.role === UserRole.user
                                });
                                newAccounts[user.username] = {
                                    ...user,
                                    role: user.role || UserRole.user,
                                    messages: [],
                                    online: true
                                };

                                // 更新进度
                                setLoadingDetails(prev => ({
                                    ...prev,
                                    progress: 60 + Math.floor((index / user_list.length) * 40)
                                }));
                            }
                        });
                        return newAccounts;
                    }, false);
                }
            }
        },
        [MessageType.USER_LIST_UPDATE]: (data) => {
            logger.info("收到用户列表更新消息:", data);
            
            if (data.content && typeof data.content === 'object') {
                const { user_list, groups } = data.content as UserListResponse;
                
                if (user_list && Array.isArray(user_list)) {
                    logger.info("开始更新用户列表, 更新数:", user_list.length);
                    updateAccounts((prevAccounts) => {
                        const updatedAccounts = { ...prevAccounts };
                        user_list.forEach((user) => {
                            if (user && user.username) {
                                logger.info("更新用户:", user.username);
                                updatedAccounts[user.username] = {
                                    ...user,
                                    messages: prevAccounts[user.username]?.messages || [],
                                    online: true
                                };
                            }
                        });
                        logger.info("用户列表更新完成");
                        return updatedAccounts;
                    }, false);
                }
            }
        },
        [MessageType.SYSTEM]: (data) => {
            const systemMessage = data as SystemMessage;
            logger.info('系统消息:', systemMessage.content);
            // 在这里添加系统消息的处理逻辑，例如显示通知
        },
        [MessageType.CHAT_HISTORY]: (data) => {
            const chatHistory = data as ChatHistoryMessage;
            const { sender, content } = chatHistory;
            
            if (Array.isArray(content)) {
                updateChatHistory(sender, content);
            } else {
                console.error('聊天历史记录格式错误：content 不是数组');
            }
        },
        [MessageType.VALIDATION]: (data) => {
            // 处理验证消息
            const validationMessage = data as any;  // 根据具体需求定义类型
            logger.info('验证消息:', validationMessage.validation_extra_data);
            // 根据需要实现具体逻辑
        },
        [MessageType.BROADCAST]: (data) => {
            // 处理广播消息，例如群发通知
            const broadcastMessage = data as any;  // 根据具体需求定义类型
            logger.info('广播消息:', broadcastMessage.content);
            // 根据需要实现具体逻辑
        },
        [MessageType.GROUP_CHAT]: (data) => {
            // TODO 组消息暂时不处理
            // logger.info("收到群聊消息:", data);
            // const groupMessage = data as GroupChatMessage;
            // handleChatMessage(MessageBase, 'group');
            // // 如果不是自己发的消息，显示通知
            // if (groupMessage.sender !== current_user) {
            //     setShouldBlink(true);
            // }
        },
        [MessageType.SELF_CHAT]: (data) => {
            const selfPrivateMessage = data as SelfPrivateChatMessage;
            logger.info('自己的私聊消息:', selfPrivateMessage);
            // 实现自己的私聊消息��理逻辑
        },
        [MessageType.ERROR]: (data) => {
            const errorMessage = data as ErrorMessage;
            console.error('错误消息:', errorMessage);
            // 实现错误消息处理逻辑
        }
    }), [current_user, selectedUser, updateAccounts, updateChatHistory, addMessage, setLoadingDetails]);

    // 然后定义消息处理函数
    const handleWebSocketMessage = useCallback((data: MessageBase) => {
        try {
            logger.info(`收到消息 (${current_user}):`, data);
            
            let parsedData = data;
            if (typeof data === 'string') {
                try {
                    parsedData = JSON.parse(data);
                } catch (e) {
                    console.error('解析消息失败:', e);
                    return;
                }
            }

            const handler = messageHandlers[parsedData.message_type];
            if (handler) {
                handler(parsedData);
            } else {
                console.warn(`未找到消息类型 ${parsedData} 的处理器`);
            }
        } catch (error) {
            console.error('处理消息时出错:', error);
        }
    }, [current_user, messageHandlers]);

    // 修改 WebSocket 连接的创建逻辑
    const { socket } = useWebSocketConnection(
        apiUrl, 
        localStorage.getItem('token'),
        current_user || '',
        handleWebSocketMessage
    ) as WebSocketConnectionReturn;

    // 增强日志记录
    useEffect(() => {
        logger.info('useWebSocketMessageHandler - 初始化参数:', {
            current_user,
            token: !!localStorage.getItem('token'),
            apiUrl
        });
    }, [current_user]);

    useEffect(() => {
        if (selectedUser) {
            logger.info('停止标题闪烁，因为选中用户变化');
            setShouldBlink(false);
        }
    }, [selectedUser]);

    return { handleWebSocketMessage };
}
