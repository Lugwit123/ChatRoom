// frontend/src/hooks/useMessageReceiver.tsx
// @ts-nocheck
import { useCallback, useState, useEffect, useMemo } from 'react';
import { useUsersQuery,invalidateMessagesQuery } from '../providers/QueryProvider';
import useCurrentSelectedUserStore from '../stores/useCurrentSelectedUserStore';
import { handleMessageUpdate } from '../utils/messageHandler';
import { logger } from '../utils/logger';
import { isLocalEnv,localHandlenewMessage} from '../utils/actions_utils';

import {
    MessageBase,
    SystemMessage,
    ChatHistoryMessage,
    MessageType,
    ErrorMessage,
    UserListResponse,
    SelfPrivateChatMessage
} from '../types/types';
import { useTitleBlink } from './useTitleBlink';
import { useChatHistory } from './useChatHistory';
import { useQueryClient } from '@tanstack/react-query';
import { QUERY_KEYS } from '../providers/QUERY_KEYS';
import { UsersInfoDictResponse } from '../types/types';
import useGlobalState from "../stores/useGlobalState";
/**
 * 自定义Hook: useMessageReceiver
 * 
 * @description
 * 用于处理从WebSocket接收到的各种类型消息。
 * 该Hook中会在顶层使用React Query的Hook来获取用户数据，并使用useChatHistory来管理聊天历史。
 * 返回的MessageReceiver函数可被用于在组件中或在WebSocket的消息回调中调用，但前提是
 * useMessageReceiver必须在React组件或自定义Hook的顶层中调用。
 * 
 * @param {any} message_data 可选的额外参数（不需要可以删除）
 * @returns {object} { MessageReceiver } - 用于处理消息的回调函数
 */

export const useMessageReceiver = (message_data: any) => {
    logger.info("进入useMessageReceiver,接受到的消息为",message_data);
    const queryClient = useQueryClient();
    // 在Hook主体中调用所有需要的Hook
    const { data: users, isLoading: isAccountsLoading } = useUsersQuery();
    const currentLoginUser = users?.current_user;
    const selectUser = useCurrentSelectedUserStore((state) => state.selectUser);
    const currentSelectedUser = useCurrentSelectedUserStore((state) => state.currentSelectedUser);
    const currentLoginUser_username = currentLoginUser ? currentLoginUser.username : '';
    const setShouldRefetchUsers = useGlobalState((state) => state.setShouldRefetchUsers);
    const [shouldBlink, setShouldBlink] = useState<boolean>(false);

    // 标题闪烁提示
    useTitleBlink({
        trigger: shouldBlink,
        blinkText: '新消息!',
        blinkInterval: 1000,
    });

    

    useEffect(() => {
        logger.info('useMessageReceiver - currentLoginUser_username:', currentLoginUser_username);
    }, [currentLoginUser_username]);

    const handleMessage_updata = useCallback((message: MessageBase) => {
        handleMessageUpdate(message, queryClient, setShouldRefetchUsers);
    }, [queryClient, setShouldRefetchUsers]);

    // 定义消息类型与处理函数的映射关系
    const Messages = useMemo<Record<MessageType, (data: MessageBase) => void>>(() => ({
        [MessageType.USER_STATUS_UPDATE]: (data) => {
            logger.info("收到用户状态更新:", data);
            const userStatus = data.content as {
                username: string;
                nickname: string;
                online: boolean;
                avatar_index: number;
            };
            
            // 使用handleMessageUpdate更新用户状态
            handleMessage_updata(data);
            
            // 记录用户上线/下线日志
            logger.info(`用户 ${userStatus.username} ${userStatus.online ? '上线' : '下线'}`);
        },
        [MessageType.PRIVATE_CHAT]: (data) => {
            logger.info("MessageReceiver - 收到私聊消息:", {
                data,
                currentLoginUser_username,
                currentSelectedUser
            });

            // 使用自定义函数失效到第四层的嵌套查询
            //invalidateMessagesQuery(queryClient, { sender: data.sender })
            handleMessage_updata(data)
            // 如果消息来自他人（而不是自己）
            if (data.sender !== currentLoginUser_username) {
                setShouldBlink(true);
            }
        },
        [MessageType.GET_USERS]: (data) => {
            logger.info("收到完整用户列表:", data);
            if (data.content && typeof data.content === 'object') {
                const { user_list } = data.content as UserListResponse;
                if (user_list && Array.isArray(user_list)) {
                    logger.info("初始化用户列表, 用户数:", user_list.length);
                    // 此处根据需要处理用户列表
                }
            }
        },
        [MessageType.USER_LIST_UPDATE]: (data) => {
            logger.info("收到用户列表更新消息:", data);
            if (data.content && typeof data.content === 'object') {
                const { user_list } = data.content as UserListResponse;
                if (user_list && Array.isArray(user_list)) {
                    logger.info("更新用户列表, 更新数:", user_list.length);
                    // 此处根据需要处理用户列表更新
                }
            }
        },
        [MessageType.SYSTEM]: (data) => {
            const systemMessage = data as SystemMessage;
            logger.info('系统消息:', systemMessage.content);
            // 处理系统消息（例如显示通知）
        },
        [MessageType.CHAT_HISTORY]: (data) => {
            const chatHistory = data as ChatHistoryMessage;
            const { sender, content } = chatHistory;

        },
        [MessageType.VALIDATION]: (data) => {
            logger.info('验证消息:', JSON.stringify(data));
            
            handleMessage_updata(data)
            // 如果消息来自他人（而不是自己）
            if (data.sender !== currentLoginUser_username) {
                setShouldBlink(true);
            }
        },
        [MessageType.BROADCAST]: (data) => {
            logger.info('广播消息:', data);
            // 处理广播消息，例如全局提示
        },
        [MessageType.GROUP_CHAT]: (data) => {
            // TODO: 组聊消息处理（目前留空）
        },
        [MessageType.SELF_CHAT]: (data) => {
            const selfPrivateMessage = data as SelfPrivateChatMessage;
            logger.info('自己的私聊消息:', selfPrivateMessage);
            // 处理自己的私聊消息逻辑
        },
        [MessageType.ERROR]: (data) => {
            const errorMessage = data as ErrorMessage;
            console.error('错误消息:', errorMessage);
            // 处理错误消息
        }
    }), [currentLoginUser_username, currentSelectedUser, handleMessage_updata]);

    // 消息接收处理函数
    // 注意：MessageReceiver是一个纯函数，不在内部调用Hooks，只使用已在useMessageReceiver中拿到的变量和函数
    const MessageReceiver = useCallback((data: MessageBase) => {
        try {
            logger.info(`收到消息 (${currentLoginUser_username}):`, data);
            let parsedData = data;

            // 如果数据是字符串则尝试解析JSON
            if (typeof data === 'string') {
                try {
                    parsedData = JSON.parse(data);
                } catch (e) {
                    console.error('解析消息失败:', e);
                    return;
                }
            }
            console.log(parsedData.popup_message, isLocalEnv);
            if (isLocalEnv ) 
                if (typeof data==="object")
                    {localHandlenewMessage(JSON.stringify(data));}
                else 
                    {localHandlenewMessage(data)}
            // 根据message_type找到对应的处理函数
            const handler = Messages[parsedData.message_type as MessageType];
            if (handler) {
                handler(parsedData);
            } else {
                console.warn(`未找到消息类型 ${parsedData.message_type} 的处理器`);
            }
        } catch (error) {
            console.error('处理消息时出错:', error);
        }
    }, [currentLoginUser_username, Messages]);

    useEffect(() => {
        logger.info('useMessageReceiver - 初始化参数:', {
            currentLoginUser_username,
            token: !!localStorage.getItem('token'),
        });
    }, [currentLoginUser_username]);

    useEffect(() => {
        if (currentSelectedUser) {
            logger.info('停止标题闪烁，因为选中用户变化');
            setShouldBlink(false);
        }
    }, [currentSelectedUser]);

    return { MessageReceiver };
};
