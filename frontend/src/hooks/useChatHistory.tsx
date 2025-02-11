// frontend/src/hooks/useChatHistory.tsx
// @ts-nocheck
import { useCallback, useRef, useState } from 'react';
import { AccountsMap, MessageBase, MessageType, MessageContentType } from '../types/types';
import { api } from '../services/api';

interface UseChatHistoryReturn {
    fetchChatHistory: (username: string) => Promise<void>;
    updateChatHistory: (username: string, messages: MessageBase[]) => void;
    addMessage: (message: MessageBase) => void;
}

export const useChatHistory = (
    token: string | null,
    setAccounts: React.Dispatch<React.SetStateAction<AccountsMap>>,
    selectedUser: string | null
): UseChatHistoryReturn => {
    // 标准化消息格式
    const normalizeMessage = useCallback((msg: any, username?: string): MessageBase => {
        // 处理消息内容
        let normalizedContent = msg.content;
        logger.info(msg.content)
        if (typeof msg.content === 'object') {
            normalizedContent = JSON.stringify(msg.content);
        }
        
        return {
            id: msg.id || `${Date.now()}_${Math.random()}`,
            sender: msg.sender || '',
            recipient: msg.recipient || username || '',
            recipient_type: msg.recipient_type || 'private',
            message_type: msg.message_type || MessageType.PRIVATE_CHAT,
            timestamp: msg.timestamp || new Date().toISOString(),
            content: normalizedContent, // 使用处理后的内容
            message_content_type: msg.message_content_type,
            status: msg.status || 'unread'
        };
    }, []);

    // 获取聊天历史
    const fetchChatHistory = useCallback(async (username: string) => {
        logger.info("useChatHistory - fetchChatHistory called:", {
            username,
            token
        });
        if (!token) {
            console.warn('等待token初始化...');
            return;
        }

        try {
            const response = await api.post('/api/get_messages', { chat_id: username });
            logger.info("useChatHistory - received chat history:", response.data);
            logger.info(response.data)
            const messages = response.data.content;
            
            if (!Array.isArray(messages)) {
                throw new Error('Invalid message format received');
            }

            const normalizedMessages = messages.map(msg => normalizeMessage(msg, username));
            logger.info("useChatHistory - normalized messages:", normalizedMessages);
            
            setAccounts(prevAccounts => {
                const updatedAccounts = {
                    ...prevAccounts,
                    [username]: {
                        ...prevAccounts[username],
                        messages: normalizedMessages,
                        unread_message_count: 0,
                    },
                };
                logger.info("useChatHistory - accounts after history update:", updatedAccounts);
                return updatedAccounts;
            });
        } catch (error: any) {
            console.error('Failed to fetch chat history:', {
                error,
                status: error.response?.status,
                data: error.response?.data,
            });
            
            if (error.response?.status === 401) {
                throw error;
            }
        }
    }, [token, setAccounts, normalizeMessage]);

    // 更新聊天历史
    const updateChatHistory = useCallback((username: string, messages: MessageBase[]) => {
        const normalizedMessages = messages.map(msg => normalizeMessage(msg, username));
        setAccounts(prevAccounts => ({
            ...prevAccounts,
            [username]: {
                ...prevAccounts[username],
                messages: normalizedMessages,
                unread_message_count: username === selectedUser ? 0 : 
                    (prevAccounts[username]?.unread_message_count || 0),
            }
        }));
    }, [setAccounts, selectedUser, normalizeMessage]);

    // 添加单条消息
    const addMessage = useCallback((message: MessageBase) => {
        logger.info("useChatHistory - addMessage called:", {
            message,
            selectedUser
        });
        const normalizedMessage = normalizeMessage(message);
        logger.info("useChatHistory - normalized message:", normalizedMessage);
        const targetUser = normalizedMessage.sender;
        
        setAccounts(prevAccounts => {
            logger.info("useChatHistory - updating accounts:", {
                prevAccounts,
                targetUser,
                isSelected: targetUser === selectedUser
            });
            const isSelected = targetUser === selectedUser;
            const updatedAccounts = {
                ...prevAccounts,
                [targetUser]: {
                    ...prevAccounts[targetUser],
                    messages: [
                        ...(prevAccounts[targetUser]?.messages || []),
                        normalizedMessage
                    ],
                    unread_message_count: isSelected ? 0 :
                        (prevAccounts[targetUser]?.unread_message_count || 0) + 1,
                }
            };
            logger.info("useChatHistory - accounts after update:", updatedAccounts);
            return updatedAccounts;
        });
    }, [setAccounts, selectedUser, normalizeMessage]);

    // 添加消息缓存机制
    const messageCache = useRef(new Map());

    // 添加分页加载
    const [page, setPage] = useState(1);
    const [hasMore, setHasMore] = useState(true);

    // 添加消息去重逻辑
    const deduplicateMessages = (messages: MessageBase[]) => {
        const uniqueMessages = new Map();
        messages.forEach(msg => {
            uniqueMessages.set(msg.id, msg);
        });
        return Array.from(uniqueMessages.values());
    };

    return {
        fetchChatHistory,
        updateChatHistory,
        addMessage
    };
};
