import { useEffect, useRef } from 'react';

export const useAutoScroll = (messages: any[]) => {
    const containerRef = useRef<HTMLDivElement>(null);
    const isMouseInComponentRef = useRef(false); // 使用 ref 代替 state

    const handleMouseEnter = () => {
        isMouseInComponentRef.current = true;
        // console.log("Mouse entered:", containerRef.current);
    };

    const handleMouseLeave = () => {
        isMouseInComponentRef.current = false;
        // console.log("Mouse left:", containerRef.current);
    };

    useEffect(() => {
        // 绑定事件监听器
        const container = containerRef.current;
        if (container) {
            container.addEventListener('mouseenter', handleMouseEnter);
            container.addEventListener('mouseleave', handleMouseLeave);
        }

        return () => {
            // 清除事件监听器
            if (container) {
                container.removeEventListener('mouseenter', handleMouseEnter);
                container.removeEventListener('mouseleave', handleMouseLeave);
            }
        };
    }, []); // 空依赖数组，确保只绑定一次

    useEffect(() => {
        // 自动滚动逻辑
        const messagesContainer = containerRef.current?.closest('.messages-container');
        console.log(isMouseInComponentRef.current,)
        console.log(messagesContainer)
        if (!isMouseInComponentRef.current && messagesContainer) {
            messagesContainer.scrollTop = messagesContainer.scrollHeight;

        }
    }, [messages]); // 仅在 messages 变化时执行

    return containerRef;
};