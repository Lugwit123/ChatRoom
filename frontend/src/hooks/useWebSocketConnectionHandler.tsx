// frontend/src/hooks/useWebSocketConnectionHandler.tsx
// @ts-nocheck
import useWebSocket from './useWebSocket';
import { useWebSocketMessageHandler } from './useWebSocketMessageHandler';
import { AccountsMap } from '../types/types';

export const useWebSocketConnectionHandler = (
    apiUrl: string,
    token: string | null,
    currentUser: string | null,
    selectedUser: string | null,
    setAccounts: React.Dispatch<React.SetStateAction<AccountsMap>>
) => {
    const { handleWebSocketMessage } = useWebSocketMessageHandler(currentUser, selectedUser, setAccounts);

    const handleOpen = () => {
        logger.info(`Socket.IO 已连接: ${currentUser}`);
    };

    const handleError = (error: any) => {
        console.error('Socket.IO 连接错误:', error);
        // 清除控制台的冗余输出
        window.logger.info = function () {};
        window.console.error = function () {};
        window.console.warn = function () {};
    };

    const handleClose = (reason: string) => {
        if (reason !== 'io client disconnect') { // 非正常关闭
            console.warn('Socket.IO 非正常关闭:', reason);
        }
    };

    const { isConnected, sendMessage } = useWebSocket(
        apiUrl,
        token,
        handleWebSocketMessage,
        handleOpen,
        handleError,
        handleClose
    );

    return { isConnected, sendMessage };
};
