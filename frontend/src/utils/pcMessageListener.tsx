import {localHandlenewMessage} from './actions_utils';
import { MessageBase,MessageType} from '../types/types';
import { apiUrl } from '../services/api';

interface ButtonData {
    buttonType: string;
    actionType: string;
    buttonId: string;
    timestamp: number;
    localPath : string;
}

interface MessageEvent {
    origin: string;
    data: {
        action: string;
        buttonData?: ButtonData;
    };
}

type DebouncedFunction = (...args: any[]) => void;

// 防抖函数
const debounce = (
    func: DebouncedFunction,
    wait: number,
    immediate: boolean = false
): DebouncedFunction => {
    let timeout: NodeJS.Timeout | null = null;

    return function executedFunction(this: any, ...args: any[]) {
        const context = this;

        // 获取当前是否应该立即执行
        const callNow = immediate && !timeout;

        // 清除之前的定时器
        const later = () => {
            timeout = null;
            // 如果不是立即执行，则在等待时间后执行
            if (!immediate) {
                func.apply(context, args);
            }
        };

        if (timeout) {
            clearTimeout(timeout);
        }
        timeout = setTimeout(later, wait);

        // 如果是立即执行，则立即调用函数
        if (callNow) {
            func.apply(context, args);
        }
    };
};

// 处理消息的具体逻辑
const handleMessage = (event: MessageEvent): void => {
    // 只处理来自指定网站的消息
    if (event.origin === apiUrl) {
        console.log("收到来自指定源的消息:", event.data);

        // 根据收到的信息执行逻辑
        if (event.data.action === "buttonClicked" && event.data.buttonData) {
            const message: MessageBase = {
                content: event.data.buttonData,
                message_type: MessageType.OPEN_PATH,
  
            };
            localHandlenewMessage(JSON.stringify(message))
        }
    }
};

// 使用改进版防抖包装消息处理函数
// 设置300ms延迟，并启用立即执行选项
const debouncedHandleMessage = debounce(handleMessage, 300, true);

// 初始化消息监听
export const initMessageListener = (): void => {
    window.addEventListener("message", debouncedHandleMessage as any);
};

// 清理消息监听
export const cleanupMessageListener = (): void => {
    window.removeEventListener("message", debouncedHandleMessage as any);
};
