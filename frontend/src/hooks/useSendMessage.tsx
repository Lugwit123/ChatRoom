// useSendMessage.tsx
import { useQueryClient, useMutation,  } from '@tanstack/react-query';
import { MessageBase, UsersInfoDictResponse,MessageDirection,MessageStatus } from '../types/types';
import { QUERY_KEYS } from '../providers/QUERY_KEYS';
import { useWebSocketQuery } from '../providers/websocketQuery';
import useGlobalState from "../stores/useGlobalState";
import { handleMessageUpdate } from '../utils/messageHandler';
import { logger } from '../utils/logger';
import { useCallback } from 'react'; // 导入 useCallback

export const useSendMessage = () => {
    const { socket } = useWebSocketQuery();
    const queryClient = useQueryClient();
    const setShouldRefetchUsers = useGlobalState((state) => state.setShouldRefetchUsers);
    /**
     * 异步函数：发送消息到服务器
     * @param newMessage {Omit<MessageBase, 'id'>} 不含ID的消息对象，服务器返回后会有ID。
     */
    const sendMessage = useCallback(
        async (newMessage: Omit<MessageBase, 'id'>): Promise<MessageBase> => {
            if (!socket) {
                throw new Error('WebSocket 未连接');
            }
            newMessage.direction = MessageDirection.REQUEST;
            return new Promise((resolve, reject) => {
                socket.emit('message', newMessage, (response) => {
                    logger.info('发送消息响应:', response);
                    if (response.status.includes(MessageStatus.SUCCESS)) {
                        resolve(response);
                    } else {
                        const errorMessage = response.status.includes(MessageStatus.FAILED)
                            ? '发送消息失败'
                            : '未知错误';
                        reject(new Error(errorMessage));
                    }
                    
                });
            });
        },
        [socket] // 依赖项数组
    );

    const mutation = useMutation({
        mutationFn: sendMessage,

        /**
         * 在请求发送之前的乐观更新
         */
        onMutate: async (newMessage: Omit<MessageBase, 'id'>) => {
            await queryClient.cancelQueries({ queryKey: [QUERY_KEYS.USERS] });
            const previousData = queryClient.getQueryData<UsersInfoDictResponse>([QUERY_KEYS.USERS]);

            const temporaryId = 'temp-' + Math.random().toString(36).substr(2, 9);

            // 假设当前用户发送消息，将消息添加到 current_user 的 messages 中
            // 根据你的业务逻辑决定将消息放入谁的消息列表里
            const currentLoginUserName = newMessage.sender; // 假设 newMessage 有 fromId 字段
            
            queryClient.setQueryData<UsersInfoDictResponse>([QUERY_KEYS.USERS], (oldData) => {
                if (!oldData) return oldData;
                const updatedData = { ...oldData };

                if (updatedData.current_user && updatedData.current_user.username === currentLoginUserName) {
                    const oldMessages = updatedData.current_user.messages || [];
                    updatedData.current_user.messages = [...oldMessages, { ...newMessage, id: temporaryId }];
                }

                return updatedData;
            });
            setShouldRefetchUsers(true)
            return { previousData, temporaryId, currentLoginUserName };
        },

        onSuccess: (data: { id?: number | string}, newMessage, context) => {
            // 使用服务器返回的真实ID替换临时ID
            queryClient.setQueryData<UsersInfoDictResponse>([QUERY_KEYS.USERS], (oldData) => {
                if (!oldData) return oldData;
                const updatedData = { ...oldData };

                // 替换 current_user 中的临时消息ID
                if (updatedData.current_user && updatedData.current_user.username === context.currentLoginUserName) {
                    if (updatedData.current_user.messages) {
                        updatedData.current_user.messages = updatedData.current_user.messages.map(msg =>
                            msg.id === context.temporaryId ? { ...msg, id: data.id } : msg
                        );
                    }
                }

                return updatedData;
            });
        },

        onError: (err, newMessage, context) => {
            if (context?.previousData) {
                queryClient.setQueryData([QUERY_KEYS.USERS], context.previousData);
            }
            logger.info('发送消息失败:', err, newMessage, context);
        },

        onSettled: () => {
            queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.USERS] });
        },
    });

    return mutation;
};
