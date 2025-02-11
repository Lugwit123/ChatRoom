import { MessageBase,MessageType,MessageContentType } from '../types/types';
import { UsersInfoDictResponse } from '../types/types';
import { QueryClient } from '@tanstack/react-query';
import { QUERY_KEYS } from '../providers/QUERY_KEYS';
import { logger } from './logger';

/**
 * 处理消息更新的工具函数
 * @param message - 接收到的消息
 * @param queryClient - React Query 客户端实例
 * @param setShouldRefetchUsers - 设置是否需要重新获取用户列表的函数
 */
export const handleMessageUpdate = (
    message: MessageBase,
    queryClient: QueryClient,
    setShouldRefetchUsers: (value: boolean) => void
) => {
    const mes_recipient = message.recipient as string;

    // 更新缓存中的用户数据
    queryClient.setQueryData<UsersInfoDictResponse>([QUERY_KEYS.USERS], (oldData) => {
        if (!oldData) return oldData;
        
        const updatedData = {
            ...oldData,
            user_map: { ...oldData.user_map },
            current_user: { ...oldData.current_user }
        };
        
        // 更新 user_map 中对应用户的 messages
        if (updatedData.user_map[mes_recipient]) {
            const oldMessages = updatedData.user_map[mes_recipient].messages || [];
            if (!oldMessages.some(m => m.id === message.id)) {
                updatedData.user_map[mes_recipient].messages = [...oldMessages, message];
            }
        }

        // 如果是当前用户自己
        if (updatedData.current_user && updatedData.current_user.username === mes_recipient) {
            const oldMessages = updatedData.current_user.messages || [];
            if (!oldMessages.some(m => m.id === message.id)) {
                updatedData.current_user.messages = [...oldMessages, message];
            }
        }
        return updatedData;
    });

    setShouldRefetchUsers(true);
    
    // 获取并打印更新后的数据
    const updatedUsers = queryClient.getQueryData([QUERY_KEYS.USERS]);
    logger.info("通过 getQueryData 获取的最新 users 数据:", updatedUsers);
}; 




