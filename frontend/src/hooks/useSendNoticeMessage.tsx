// 封装发送消息逻辑为 Hook
import { useSendMessage } from '../hooks/useSendMessage';
import { MessageBase, 
    MessageType, 
    MessageContentType, 
    UserBaseAndStatus,
    MessageStatus } from '../types/types';
import { logger } from '../utils/logger';
import { useWebSocketQuery } from '../providers/websocketQuery';
export const useHandleSendNoticeMessage = () => {

    const { socket } = useWebSocketQuery();
    const handleSendNoticeMessage = async (message: MessageBase) => {
        // 构建新消息对象 (不包含 id)
        const newMessage: Omit<MessageBase, 'id'> = {
            ...message,
            message_type: MessageType.VALIDATION,
            message_content_type: MessageContentType.HTML,
            timestamp:new Date().toISOString(),
        };

        logger.info('待发送消息:', newMessage);

        // 发送消息逻辑
        try {
            socket.emit('message', newMessage, (response) => {
                logger.info('发送消息响应:', response);
                if (response.status.includes(MessageStatus.SUCCESS)) {
                    console.log("发送成功")
                } else {
                    const errorMessage = response.status.includes(MessageStatus.FAILED)
                        ? '发送消息失败'
                        : '未知错误';
                    console.log(errorMessage);
                }
                
            });
        } catch (error) {
            alert(`发送消息失败，请重试。${error}`);
        }
    };

    return handleSendNoticeMessage;
};