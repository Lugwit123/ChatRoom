// frontend/src/hooks/useTitleBlink.ts
import { useEffect, useRef } from 'react';
import { logger } from '../utils/logger';
interface UseTitleBlinkProps {
    trigger: boolean;
    blinkText?: string;
    blinkInterval?: number;
}

export const useTitleBlink = ({
    trigger,
    blinkText = 'New Message!',
    blinkInterval = 1000,
}: UseTitleBlinkProps) => {
    const originalTitle = useRef<string>(document.title);
    const blinkIntervalId = useRef<number | null>(null);

    useEffect(() => {
        logger.info(`useTitleBlink trigger: ${trigger}`);

        // 处理页面可见性变化
        const handleVisibilityChange = () => {
            if (document.hidden) {
                // 页面不可见时,如果 trigger 为 true 则开始闪烁
                if (trigger && blinkIntervalId.current === null) {
                    logger.info('页面不可见,开始标题闪烁');
                    blinkIntervalId.current = window.setInterval(() => {
                        document.title = document.title === originalTitle.current
                            ? blinkText
                            : originalTitle.current;
                    }, blinkInterval);
                }
            } else {
                // 页面可见时停止闪烁并恢复原标题
                if (blinkIntervalId.current !== null) {
                    logger.info('页面可见,停止标题闪烁');
                    clearInterval(blinkIntervalId.current);
                    blinkIntervalId.current = null;
                    document.title = originalTitle.current;
                }
            }
        };

        // 添加可见性变化事件监听
        document.addEventListener('visibilitychange', handleVisibilityChange);

        // 初始检查 - 如果页面一开始就不可见且 trigger 为 true,则开始闪烁
        if (document.hidden && trigger && blinkIntervalId.current === null) {
            logger.info('初始状态页面不可见,开始标题闪烁');
            blinkIntervalId.current = window.setInterval(() => {
                document.title = document.title === originalTitle.current
                    ? blinkText
                    : originalTitle.current;
            }, blinkInterval);
        }

        // 清理函数
        return () => {
            document.removeEventListener('visibilitychange', handleVisibilityChange);
            if (blinkIntervalId.current !== null) {
                clearInterval(blinkIntervalId.current);
                blinkIntervalId.current = null;
                document.title = originalTitle.current;
            }
        };
    }, [trigger, blinkText, blinkInterval]);
};
