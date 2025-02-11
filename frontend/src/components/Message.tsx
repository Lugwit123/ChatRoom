// Message.tsx
import React, { useEffect, useRef, useState, forwardRef } from 'react';
import JSON5 from 'json5';
import { MessageBase, MessageType, MessageStatus } from '../types/types';
import DOMPurify from 'dompurify';
import './Message.css';
import useCurrentSelectedUserStore from '../stores/useCurrentSelectedUserStore';
import { useUsersQuery } from '../providers/QueryProvider';
import { logger } from '../utils/logger';
import { useAutoScroll } from '../hooks/useAutoScroll';
import { is_developenv } from '../utils/actions_utils';
import useVisibility from '../hooks/useVisibility';
import { initMessageListener, cleanupMessageListener } from '../utils/pcMessageListener';
// import { markMessageAsRead } from '../utils/messageUtils'; // 暂时注释

interface SingleMessageProps {
    message: MessageBase;
}

const SingleMessage = forwardRef<HTMLDivElement, SingleMessageProps>(({ message }, ref) => {
    const currentSelectedUser = useCurrentSelectedUserStore((state) => state.currentSelectedUser);
    const isOwnMessage = message.sender !== currentSelectedUser?.username;
    let message_content = "";

    if (message.message_type === MessageType.VALIDATION) {
        try {
            if (typeof message.content === 'string') {
                const contentObj = JSON5.parse(message.content);
                message_content = contentObj.url;
            } else {
                message_content = message.content.url;
            }
        } catch (error) {
            logger.error('解析消息内容失败:', error);
            message_content = '消息格式错误';
        }
        message_content = `<iframe src="${message_content}" width="500px"  allow="clipboard-write">></iframe>`;
    } else {
        message_content = message.content as string;
    }

    const messageClass = isOwnMessage ? 'ownMessage' : 'otherMessage';
    const [isRead, setIsRead] = useState<boolean>(message.status?.includes(MessageStatus.READ) || false);

    const sanitizeConfig = {
        ADD_TAGS: ['table', 'thead', 'tbody', 'tr', 'th', 'td', 'button', 'script', 'iframe'],
        ADD_ATTR: ['colspan', 'rowspan', 'width', 'style', 'align', 'class', 'onclick'],
    };

    const sanitizedContent = DOMPurify.sanitize(message_content, sanitizeConfig);

    const { ref: visibilityRef, isVisible } = useVisibility({
        threshold: 0.5, // 当元素有 50% 可见时触发
    });

    useEffect(() => {
        let timer: NodeJS.Timeout;

        if (isOwnMessage && isVisible && !isRead) {
            timer = setTimeout(() => {
                // 这里假设你有一个方法来更新消息状态，比如通过上下文或全局状态管理
                // 示例：markMessageAsRead(message.id);
                // 由于你注释掉了 API 调用，暂时直接修改
                // 注意：直接修改 props 会导致不可预期的行为，建议使用状态或全局管理
                // 这里仅为示例
                message.status = [...(message.status || []), MessageStatus.READ];
                setIsRead(true);
            }, 1000); // 延迟0.5秒
        }

        return () => {
            if (timer) {
                clearTimeout(timer); // 清除定时器以防止内存泄漏
            }
        };
    }, [isVisible, isRead, message, isOwnMessage]);

    // 合并多个 refs 的辅助函数
    const setRefs = (el: HTMLDivElement | null) => {
        // 处理 forwarded ref
        if (typeof ref === 'function') {
            ref(el);
        } else if (ref) {
            (ref as React.MutableRefObject<HTMLDivElement | null>).current = el;
        }

        // 处理 visibilityRef
        if (visibilityRef) {
            (visibilityRef as React.MutableRefObject<HTMLDivElement | null>).current = el;
        }
    };

    return (
        
        <div className='message' ref={setRefs}>
            {/* 只在自己发送的消息上显示已读/未读状态 */}
            {isOwnMessage && (
                    <div className={`message-status ${isRead ? 'read' : 'unread'}`}>
                        {isRead ? '已读' : '未读'}
                    </div>
                )}
            <div className={`message-main-body ${messageClass}`}>
                <div className="message-avatar">
                    <img src={`/avatars/avatar${1}.png`} alt="avatar" />
                </div>
                <div className="message-content">
                    
                    <div
                        className="message-text"
                        dangerouslySetInnerHTML={{ __html: sanitizedContent }}
                    ></div>
                    <button className="parse-path-button">解析路径</button>
                    <span className="message-timestamp">
                        {new Date(message.timestamp).toLocaleString()}
                    </span>
                </div>
            </div>
        </div>
    );
});

const Message = () => {
    logger.info("渲染Message组件");

    useEffect(() => {
        logger.info('Message组件加载');
        // 初始化消息监听器
        initMessageListener();

        return () => {
            logger.info('Message组件卸载');
            // 清理消息监听器
            cleanupMessageListener();
        };
    }, []);

    const currentSelectedUser = useCurrentSelectedUserStore((state) => state.currentSelectedUser);
    const { data: users, isLoading: isAccountsLoading } = useUsersQuery();
    logger.info(users);
    const currentLoginUser = users?.current_user;
    let messages = users?.user_map[currentSelectedUser?.username]?.messages;
    const containerRef = useAutoScroll(messages);
    console.log("containerRef.current", containerRef.current);

    const messageRefs = useRef<Record<number, HTMLDivElement | null>>({});

    useEffect(() => {
        logger.info('Message组件依赖项变化:', {
            users: users,
            currentSelectedUser: currentSelectedUser,
            messages: messages,
            isAccountsLoading
        });
    }, [messages]);

    const [targetMessageIndex, setTargetMessageIndex] = useState<number | ''>(1);
    (window as any).setTargetMessageIndex = setTargetMessageIndex;

    const scrollToMessage = () => {
        if (typeof targetMessageIndex !== 'number' || targetMessageIndex < 1 || targetMessageIndex > (messages?.length || 0)) {
            alert('请输入有效的消息序号');
            return;
        }

        const index = targetMessageIndex - 1;
        const targetRef = messageRefs.current[index];
        if (targetRef) {
            targetRef.scrollIntoView({ behavior: 'smooth', block: 'start' });
            targetRef.classList.add('highlight');
            setTimeout(() => {
                targetRef.classList.remove('highlight');
            }, 2000);
        } else {
            alert('未找到指定的消息');
        }
    };

    return (
        <div className="message-container">
            <div className="user-card" ref={containerRef}>
                <div className="messages_single">
                    {messages && messages.length > 0 ? (
                        messages.map((message: MessageBase, index: number) => (
                            <SingleMessage
                                key={message.id}
                                message={message}
                                ref={(el) => (messageRefs.current[index] = el)}
                            />
                        ))
                    ) : (
                        <p>暂无消息</p>
                    )}
                </div>
            </div>
            {/* {is_developenv && <div className="scroll-to-message-fixed">
                <input
                    type="number"
                    min="1"
                    max={messages ? messages.length : 1}
                    placeholder="输入消息序号"
                    value={targetMessageIndex}
                    onChange={(e) => {
                        const value = e.target.value;
                        setTargetMessageIndex(value === '' ? '' : Number(value));
                    }}
                    onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                            scrollToMessage();
                        }
                    }}
                />
                <button onClick={scrollToMessage}>滚动到消息</button>
            </div>} */}
        </div>
    );
};

// 开启渲染追踪
Message.whyDidYouRender = true;
export default Message;
