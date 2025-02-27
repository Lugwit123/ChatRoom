// @ts-nocheck
import React, { useState, useEffect, useRef } from 'react';
import './ChatPanel.css';
import BaseMessage from './Message';
import { 
    MessageBase, 
    UserBaseAndDevices, 
    MessageType, 
    MessageContentType,
    AccountsMap
} from '../types/types';
import MyWangEditor from './MyWangEditor';
import { useWebSocketConnectionHandler } from '../hooks';

interface ChatPanelProps {
    account: UserBaseAndDevices | null;
    current_user: string | null;
    wsConnected: boolean;
    handleSendMessage: (message: MessageBase) => void;
    updateAccountsList: React.Dispatch<React.SetStateAction<AccountsMap>>;
    setLoadingDetails: React.Dispatch<React.SetStateAction<{
        step: string;
        details: string;
        progress: number;
    }>>;
}

const ChatPanel: React.FC<ChatPanelProps> = ({
    account,
    current_user,
    wsConnected,
    handleSendMessage,
    updateAccountsList,
    setLoadingDetails
}) => {
    const [editorContent, setEditorContent] = useState(''); // 管理编辑器内容的状态
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const [showNewMessageIndicator, setShowNewMessageIndicator] = useState(false); // 控制是否显示“有新消息”提示
    const [message, setMessage] = useState('');
    const { 
        socket, 
        connected: socketConnected, 
        getConnectionInfo
    } = useWebSocketConnectionHandler(
        current_user,
        account?.username,
        updateAccountsList,
        setLoadingDetails
    );
    const { sid } = getConnectionInfo();

    // 滚动到最新消息
    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
        setShowNewMessageIndicator(false); // 滚动后隐藏提示
    };

    // 当 account?.messages 更新时，显示"有新消息"提示
    useEffect(() => {
        if (account?.messages) {
            setShowNewMessageIndicator(true);
        }
    }, [account?.messages]);

    // 切换用户时滚动到底部
    useEffect(() => {
        if (account) {
            scrollToBottom();
        }
    }, [account]);

    // 统一的消息发送处理函数
    const sendMessage = (content: string, isHtml: boolean = true) => {
        if (!content.trim() || !wsConnected) {
            logger.info("消息为空或未连接:", {
                content: content.trim(),
                wsConnected
            });
            return;
        }

        logger.info("准备发送消息:", {
            current_user,
            recipient: account?.username,
            content: content.trim(),
            isHtml
        });

        // 构造消息对象
        const messageData: MessageBase = {
            message_type: MessageType.PRIVATE_CHAT,
            sender: current_user || 'unknown',
            recipient: account?.username || '',
            content: content.trim(),
            timestamp: new Date().toISOString(),
            recipient_type: 'private',
            message_content_type: MessageContentType.HTML,
            status: 'unread'
        };

        logger.info("发送消息数据:", messageData);

        try {
            handleSendMessage(messageData);
            logger.info("消息已发送");
        } catch (error) {
            console.error("发送消息失败:", error);
        }
    };

    // 处理富文��编辑器发送
    const onSend = () => {
        if (editorContent.trim()) {
            // 发送 HTML 格式的消息
            sendMessage(editorContent, true);
            setEditorContent(''); // 发送后清空编辑器内容
        } else {
            alert('消息不能为空');
        }
    };

    // 处理普通文本输入框发送
    const handleInputSend = () => {
        if (message.trim()) {
            // 发送纯文本格式的消息
            sendMessage(message, false);
            setMessage(''); // 发送后清空输入框
        }
    };

    // 添加键盘事件处理
    const handleKeyPress = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleInputSend();
        }
    };

    // 添加用于日志的 useEffect
    useEffect(() => {
        if (account) {
            logger.info('ChatPanel messages updated:', account.messages);
        }
    }, [account?.messages]);

    return (
        <div className="chat-panel-container">
            {!account ? (
                <p>正在加载账户信息...</p>
            ) : (
                <>
                    <div className="messages-container">
                        {account.messages?.map((msg: MessageBase, index: number) => (
                            <Message
                                key={`${msg.sender}-${msg.timestamp}-${index}`}
                                message={msg}
                                current_user={current_user}
                            />
                        ))}
                        <div ref={messagesEndRef} />
                    </div>

                    {/* 输入区域始终显示 */}
                    <div className="input-container">
                        <MyWangEditor
                            className="MyWangEditor_ins"
                            value={editorContent}
                            onChange={setEditorContent}
                        />
                        <button
                            className="send-button"
                            onClick={onSend}
                            disabled={!wsConnected || !account}
                            aria-label="发送消息"
                        >
                            发送
                        </button>
                    </div>
                </>
            )}
        </div>
    );
};

export default ChatPanel;
