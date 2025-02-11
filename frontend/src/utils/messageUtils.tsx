import React from 'react';
import { MessageBase, AccountsMap, MessageType, MessageContentType, UserBaseAndStatus } from '../types/types';

// 使用 React Query 的变更后刷新数据
import axios from 'axios';
import { QueryClient } from '@tanstack/react-query';
import { logger } from './logger'; // 确保你有一个 logger 工具

// 添加接口定义
export interface SendMessageParams {
    message: string;
    recipient: string;
    sender: string | UserBaseAndStatus;
    sendMessageFn: (event: string, payload: MessageBase) => void;
    recipientType: 'group' | 'private' | 'all';
    groupNames?: string[];
    messageType: MessageType.PRIVATE_CHAT | MessageType.GROUP_CHAT | MessageType.BROADCAST;
    contentType: MessageContentType.PLAIN_TEXT | MessageContentType.RICH_TEXT | MessageContentType.HTML;
}


// utils/messageUtils.tsx



/**
 * 标记消息为已读
 * @param messageId 消息的唯一标识符
 * @param queryClient React Query 的 QueryClient 实例，用于刷新查询
 */
// export const markMessageAsRead = async (messageId: string, queryClient: QueryClient) => {
//     try {
//         // 发送 POST 请求到后端 API，标记消息为已读
//         await axios.post('/api/messages/read', { messageId });

//         // 刷新相关的查询数据，假设使用 'users' 作为查询键
//         queryClient.invalidateQueries(['users']);

//         // 记录成功日志
//         logger.info(`消息 ${messageId} 已标记为已读`);
//     } catch (error) {
//         // 记录错误日志
//         logger.error('标记消息为已读失败:', error);
//         // 根据需要，你可以在这里抛出错误或者返回失败状态
//         throw error;
//     }
// };

