// frontend/src/components/ChatPanel.tsx
import React, { useRef, useEffect, useCallback } from 'react';
import './ChatPanel.css';
import useCurrentSelectedUserStore from '../stores/useCurrentSelectedUserStore';
import BaseMessage from './Message';
import { 
    MessageBase, 
    UserBaseAndStatus, 
    MessageType, 
    MessageContentType,
    popup_message
} from '../types/types';
import MyWangEditor, { MyWangEditorHandle } from './MyWangEditor';
import { useUsersQuery } from '../providers/QueryProvider';
import { useSendMessage } from '../hooks/useSendMessage';
import { logger } from '../utils/logger';
import { useHandleSendNoticeMessage } from '../hooks/useSendNoticeMessage';
import { useHotkeys } from 'react-hotkeys-hook';
import debounce from 'lodash/debounce';
import { FixedSizeList as List } from 'react-window'; // 确保已安装 react-window

// 声明全局Window接口扩展
declare global {
    interface Window {
        sendNormalMessage: () => void;
        sendPopupMessage: () => void;
        sendRemoteControlMessage: () => void;
        setEditorContent: (content: string) => void;
        setCurrentSelectedUser: (username: string) => void;
        getCurrentSelectedUser: () => string | undefined;
    }
}

interface SendMessageOptions {
    event?: React.MouseEvent | null;
    send_popup?: boolean;
    remote_control?: boolean;
}

const ChatPanel: React.FC = () => {
    // 组件挂载和卸载时记录日志
    useEffect(() => {
        logger.info('ChatPanel组件挂载');
        return () => {
            logger.info('ChatPanel组件卸载');
        };
    }, []);

    // 获取用户信息
    const { data: users, isLoading: isAccountsLoading } = useUsersQuery();
    const currentLoginUser = users?.current_user;

    // 获取当前选中用户
    const currentSelectedUser = useCurrentSelectedUserStore((state) => state.currentSelectedUser);

    // 获取设置当前选中用户的函数
    const setCurrentSelectedUser = useCurrentSelectedUserStore((state) => state.setCurrentSelectedUser);

    // 引用富文本编辑器对象
    const editorRef = useRef<MyWangEditorHandle>(null);

    // 获取发送消息的mutation
    const sendMessageMutation = useSendMessage();
    const handleSendNoticeMessage = useHandleSendNoticeMessage();

    /**
     * handleSendMessage函数
     * 
     * 功能:
     * - 获取编辑器内容
     * - 校验当前选中用户与消息内容
     * - 通过sendMessageMutation发送消息
     */
    const handleSendMessage = useCallback(async ({
        event = null,
        send_popup = false,
        remote_control = false
    }: SendMessageOptions = {}) => {
        if (event) {
            event.preventDefault(); // 如果有 event，则阻止默认行为
        }

        if (!currentSelectedUser) {
            alert('请选择一个用户进行聊天。');
            return;
        }

        const content = editorRef.current?.getContent();
        console.log('HTML content:', content);
        console.log('Text content:', editorRef.current?.getText());
        
        // 检查内容是否为空（允许只有图片的消息）
        if (!content || content.trim() === '<p><br></p>') {
            alert('消息内容不能为空。');
            return;
        }
        if (remote_control) send_popup=true
        // 构建新消息对象(不包含id)
        const newMessage: Omit<MessageBase, 'id'> = {
            content: content,
            sender: currentLoginUser?.username, // 使用当前登录用户的用户名作为发送者
            recipient: currentSelectedUser.username,
            timestamp: new Date().toISOString(),
            message_type: remote_control ? MessageType.REMOTE_CONTROL : MessageType.PRIVATE_CHAT,
            message_content_type: MessageContentType.HTML, // 确保属性名正确
            popup_message: send_popup
        };

        logger.info('待发送消息:', newMessage);

        // 发送消息逻辑, 调用Mutation
        try {
            sendMessageMutation.mutate(newMessage, {
                onSuccess: (data) => {
                    logger.info('消息发送成功，服务器返回数据:', data);
                    // 清空编辑器内容
                    (editorRef as any).current?.clearContent();
                },
                onError: (error: Error) => {
                    console.error('发送消息失败:', error);
                    alert(`发送消息失败，请重试。${error.message}`);
                },
            });
        } catch (error) {
            console.error('发送消息失败:', error);
            alert(`发送消息失败，请重试。${error instanceof Error ? error.message : ''}`);
        }
    }, [currentSelectedUser, currentLoginUser, sendMessageMutation]);

    // 暴露发送消息函数到window对象
    useEffect(() => {
        // 使用稳定的函数引用
        const stableSendNormalMessage = () => handleSendMessage({});
        const stableSendPopupMessage = () => handleSendMessage({ send_popup: true });
        const stableSendRemoteControlMessage = () => handleSendMessage({ remote_control: true });
        const stableSetEditorContent = (content: string) => {
            editorRef.current?.setContent(content);
        };

        // 设置当前选中用户的函数
        const stableSetCurrentSelectedUser = (username: string) => {
            // 从users中找到对应的用户
            const user = users?.all_users.find(u => u.username === username);
            if (user) {
                setCurrentSelectedUser(user);
            } else {
                console.error(`User ${username} not found`);
            }
        };

        // 获取当前选中用户的函数
        const stableGetCurrentSelectedUser = () => {
            return currentSelectedUser?.username;
        };

        // 暴露函数到window对象
        window.sendNormalMessage = stableSendNormalMessage;
        window.sendPopupMessage = stableSendPopupMessage;
        window.sendRemoteControlMessage = stableSendRemoteControlMessage;
        window.setEditorContent = stableSetEditorContent;
        window.setCurrentSelectedUser = stableSetCurrentSelectedUser;
        window.getCurrentSelectedUser = stableGetCurrentSelectedUser;

        // 清理函数
        return () => {
            delete window.sendNormalMessage;
            delete window.sendPopupMessage;
            delete window.sendRemoteControlMessage;
            delete window.setEditorContent;
            delete window.setCurrentSelectedUser;
            delete window.getCurrentSelectedUser;
        };
    }, [handleSendMessage, setCurrentSelectedUser, users, currentSelectedUser]);

    // 使用 lodash.debounce 为 handleSendMessage 添加防抖
    const debouncedHandleSendMessage = useCallback(
        debounce((options: SendMessageOptions) => {
            handleSendMessage(options);
        }, 300),
        [handleSendMessage]
    );

    // 创建辅助函数以简化调用
    const sendNormalMessage = useCallback(() => debouncedHandleSendMessage({}), [debouncedHandleSendMessage]);
    const sendPopupMessage = useCallback(() => debouncedHandleSendMessage({ send_popup: true }), [debouncedHandleSendMessage]);
    const sendRemoteControlMessage = useCallback(() => debouncedHandleSendMessage({ remote_control: true }), [debouncedHandleSendMessage]);

    return (
        <div className="chat-panel-container">
            <div className="messages-container">
                <Message />
            </div>

            {/* 输入区域，用于输入并发送消息 */}
            <div className="input-container">
                <MyWangEditor
                    className="MyWangEditor_ins"
                    ref={editorRef}
                    onSend={sendNormalMessage}
                />
                <div className="send-button-container">
                    <button
                        className="send-button"
                        onClick={sendNormalMessage} // 发送普通消息
                        aria-label="发送消息"
                    >
                        发送
                    </button>
                    <button
                        onClick={sendPopupMessage} // 发送通知
                        aria-label="发送通知"
                    >
                        发送通知
                    </button>
                    <button
                        onClick={sendRemoteControlMessage} // 远程协助
                        aria-label="远程协助"
                    >
                        远程协助
                    </button>
                    <button>
                        占个位置
                    </button>
                </div>
            </div>
        </div>
    );
};

export default React.memo(ChatPanel);
