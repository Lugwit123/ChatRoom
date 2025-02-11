// frontend/src/hooks/useWebSocket.tsx

import { useEffect, useRef, useState, useCallback } from 'react';
import { io, Socket } from 'socket.io-client';

type OnMessageCallback<T = unknown> = (data: T) => void;
type OnOpenCallback = () => void;
type OnErrorCallback = (error: any) => void;
type OnCloseCallback = (reason: string) => void;

interface UseSocketReturn {
    isConnected: boolean;
    sendMessage: (event: string, msg: any) => void;
}

const MAX_RETRIES = 5;
const INITIAL_RETRY_DELAY = 1000; // 1 second

function useWebSocket(
    apiUrl: string,
    token: string | null,
    onMessage: OnMessageCallback,
    onOpen: OnOpenCallback,
    onError: OnErrorCallback,
    onClose: OnCloseCallback
): UseSocketReturn {
    const socketRef = useRef<Socket | null>(null);
    const retryCountRef = useRef<number>(0);
    const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
    const [isConnected, setIsConnected] = useState<boolean>(false);

    // Store the latest callbacks in refs to avoid re-creating listeners
    const onMessageRef = useRef<OnMessageCallback>(onMessage);
    const onOpenRef = useRef<OnOpenCallback>(onOpen);
    const onErrorRef = useRef<OnErrorCallback>(onError);
    const onCloseRef = useRef<OnCloseCallback>(onClose);

    useEffect(() => {
        onMessageRef.current = onMessage;
    }, [onMessage]);

    useEffect(() => {
        onOpenRef.current = onOpen;
    }, [onOpen]);

    useEffect(() => {
        onErrorRef.current = onError;
    }, [onError]);

    useEffect(() => {
        onCloseRef.current = onClose;
    }, [onClose]);

    const connect = useCallback(() => {
        if (!token) {
            console.log("Token为空，跳过Socket.IO连接。");
            return;
        }

        console.log('连接到 Socket.IO 服务器:', apiUrl);
        const socket = io(apiUrl, {
            auth: {token :token},
            transports: ['websocket'], // 强制使用 WebSocket，避免长轮询
            reconnection: true, // 我们自己管理重连
            reconnectionDelay: 10500,
        });

        socketRef.current = socket;

        socket.on('connect', () => {
            console.log('Socket.IO连接成功');
            setIsConnected(true);
            retryCountRef.current = 0; // 重置重试计数
            onOpenRef.current();
        });

        socket.on('message', (data: any) => {
            console.log('收到Socket.IO消息:', data);
            onMessageRef.current(data);
        });

        socket.on('chat_history', (data: any) => {
            console.log('收到聊天历史:', data);
            onMessageRef.current(data);
        });

        socket.on('disconnect', (reason: string) => {
            console.log('Socket.IO已断开:', reason);
            setIsConnected(false);
            onCloseRef.current(reason);

            if (reason !== 'io client disconnect') { // 非正常断开
                if (retryCountRef.current < MAX_RETRIES) {
                    const retryDelay = INITIAL_RETRY_DELAY * Math.pow(2, retryCountRef.current);
                    console.log(`将在${retryDelay / 1000}秒后尝试重新连接...`);
                    reconnectTimeoutRef.current = setTimeout(() => {
                        retryCountRef.current += 1;
                        connect();
                    }, retryDelay);
                } else {
                    console.log('已达到最大重试次数，不再尝试重新连接。');
                }
            }
        });

        socket.on('error', (error: any) => {
            console.error('Socket.IO遇到错误:', error);
            onErrorRef.current(error);
        });
    }, [apiUrl, token]);

    useEffect(() => {
        console.log('useWebSocket useEffect', token);
        if (!token) return;

        connect();

        return () => {
            if (reconnectTimeoutRef.current !== null) {
                clearTimeout(reconnectTimeoutRef.current);
            }
            if (socketRef.current) {
                socketRef.current.disconnect();
            }
        };
    }, [connect, token]);

    const sendMessage = useCallback((event: string, msg: any) => {
        console.log(`尝试发送消息 (${event}):`, msg);
        if (socketRef.current && socketRef.current.connected) {
            console.log(`消息已发送 (${event}):`, msg);
            socketRef.current.emit(event, msg);
        } else {
            console.log('Socket.IO 是否连接',socketRef.current.connected);
            console.log('Socket.IO 未连接，无法发送消息。');
        }
    }, []);

    return { isConnected, sendMessage };
}

export default useWebSocket;
