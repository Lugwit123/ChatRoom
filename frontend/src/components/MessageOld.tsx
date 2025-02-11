import React, { useEffect, useRef } from 'react';
import { MessageBase } from '../types/types';
import DOMPurify from 'dompurify';
import './Message.css';

interface MessageProps {
  message: MessageBase;
  current_user: string;
}

const Message: React.FC<MessageProps> = ({ message, current_user }) => {
  const containerRef = useRef<HTMLDivElement>(null);

  // 判断消息类型
  const isOwnMessage = message.sender === current_user;

  const messageClass = isOwnMessage ? 'ownMessage' : 'otherMessage';

  // 配置 DOMPurify，允许表格等标签和属性
  const sanitizeConfig = {
    ADD_TAGS: ['table', 'thead', 'tbody', 'tr', 'th', 'td', 'button', 'script','iframe'],
    ADD_ATTR: ['colspan', 'rowspan', 'width', 'style', 'align', 'class', 'onclick'],
  };

  // 消毒 HTML 内容
  const sanitizedContent = DOMPurify.sanitize(message.content, sanitizeConfig);

  useEffect(() => {
    const container = containerRef.current;
  
    // 解析并动态插入 <script> 标签
    if (container) {
      const scripts = container.querySelectorAll('script');
      scripts.forEach((script) => {
        const newScript = document.createElement('script');
        newScript.textContent = script.textContent;
        document.body.appendChild(newScript);
  
        // 移除插入的脚本以避免污染全局
        document.body.removeChild(newScript);
      });
    }
  }, [message.content]);

  return (
    <div className={`message ${messageClass}`}>
      <div className="message-avatar">
        <img src={`/avatars/avatar${1}.png`} alt="avatar" />
      </div>
      <div className="message-content" ref={containerRef}>
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
  );
};

export default Message;
