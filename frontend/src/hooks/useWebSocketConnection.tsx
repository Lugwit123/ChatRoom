// frontend/src/hooks/useWebSocketConnection.tsx
// @ts-nocheck

import { useCallback, useEffect, useRef, useState } from 'react';
import { io, Socket } from 'socket.io-client';
import { MessageBase } from '../types/types';
import { logger } from '../utils/logger';

const apiUrl = import.meta.env.VITE_API_URL;

export type WebSocketConnectionReturn = {
    /** 当前WebSocket是否已连接 */
    isWsConnected: boolean;
    /** 通过WebSocket发送消息的函数 */
    message: (event: string, payload: MessageBase) => void;
    /** 当前的Socket实例 */
    socket: Socket | null;
    /** 控制模态框是否打开的状态 */
    isModalOpen: boolean;
    /** 设置模态框状态的函数 */
    setIsModalOpen: (open: boolean) => void;
    /** 当前连接状态，'connecting' | 'connected' | 'disconnected' | 'restored' */
    connectionStatus: 'connecting' | 'connected' | 'disconnected' | 'restored';
    /** 历史token信息数组 */
    tokenHistory: Array<{
        token: string;
        timestamp: string;
    }>;
};

/**
 * 自定义Hook：useWebSocketConnection
 * 
 * @description
 * 本Hook用于处理WebSocket连接的建立、重连、消息接收与发送逻辑。
 * 它内部负责根据当前token和allowConnect决定是否自动连接WebSocket，
 * 并在连接成功后通过事件监听来处理消息、错误和断开连接等事件。
 * 
 * @param {object} params
 * @param {(data:any)=>void} [params.handleReciveMessage=defaultOnMessage]
 *        接收到WebSocket消息时的回���函数。
 * @param {boolean} [params.allowConnect=true] 
 *        是否允许进行WebSocket连接。
 * 
 * @returns {WebSocketConnectionReturn} 包含WebSocket连接状态和操作函数的对象
 */
export const useWebSocketConnection = ({
    handleReciveMessage = defaultOnMessage,
    allowConnect = true,
}: {
    handleReciveMessage?: (data: any) => void;
    allowConnect?: boolean;
}): WebSocketConnectionReturn => {
    // 从本地存储中获取token和current_user，用于鉴权
    const token = localStorage.getItem('token');
    const current_user = localStorage.getItem('current_user');
    
    // isWsConnected：标记WebSocket当前是否连接
    const [isWsConnected, setIsConnected] = useState(false);
    // isModalOpen：用于控制模态框
    const [isModalOpen, setIsModalOpen] = useState(false);
    // connectionStatus：记录连接状态(connected、disconnected、connecting、restored)
    const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected' | 'restored'>('disconnected');
    
    // 使用ref来存储socket实例和重连次数
    const socketRef = useRef<Socket | null>(null);
    const reconnectAttemptsRef = useRef(0);
    const maxReconnectAttempts = 5;

    /**
     * 建立或重新建立Socket连接的函数
     */
    const connectSocket = useCallback(() => {
        if (!allowConnect || !token) {
            logger.debug('WebSocket: 跳过连接', {
                allowConnect,
                hasToken: !!token
            });
            return null;
        }

        if (socketRef.current?.connected) {
            logger.debug('WebSocket: 已经连接，跳过重连');
            return socketRef.current;
        }

        logger.info('WebSocket: 开始创建新连接');
        const socket = io(apiUrl, {
            auth: { token },
            transports: ['websocket'],
            reconnection: true,
            reconnectionAttempts: maxReconnectAttempts,
            reconnectionDelay: 1000,
            timeout: 10000,
            autoConnect: true,
        });

        // 监听连接成功事件
        socket.on('connect', () => {
            logger.info('WebSocket: 连接成功', {
                socketId: socket.id,
                current_user: current_user || 'unknown',
                reconnectAttempts: reconnectAttemptsRef.current
            });
            setIsConnected(true);
            setConnectionStatus('connected');
            reconnectAttemptsRef.current = 0;
        });

        // 监听断开连接事件
        socket.on('disconnect', (reason) => {
            logger.info('WebSocket: 连接断开', {
                reason,
                socketId: socket.id,
                timestamp: new Date().toISOString(),
                stack: new Error().stack
            });
            setIsConnected(false);
            setConnectionStatus('disconnected');
        });

        // 监听连接错误事件
        socket.on('connect_error', (error: Error) => {
            logger.info('WebSocket: 连接错误', {
                error: error.message,
                name: error.name,
                socketId: socket.id,
                current_user: current_user || 'unknown',
                token: !!token,
                apiUrl,
                attempts: reconnectAttemptsRef.current + 1,
                timestamp: new Date().toISOString()
            });
            setIsConnected(false);
            setConnectionStatus('disconnected');
            reconnectAttemptsRef.current++;

            // 达到最大重连次数后关闭socket
            if (reconnectAttemptsRef.current >= maxReconnectAttempts) {
                logger.info('WebSocket: 达到最大重连次数', {
                    maxAttempts: maxReconnectAttempts,
                    currentAttempts: reconnectAttemptsRef.current,
                    token: !!token,
                    apiUrl
                });
                socket.close();
            }
        });

        // 监听WebSocket错误事件
        socket.on('error', (error) => {
            logger.info('WebSocket: 错误', {
                error,
                socketId: socket.id,
                current_user: current_user || 'unknown'
            });
        });

        // 监听消息事件，并调用handleReciveMessage处理接收到的消息数据
        socket.on('message', (data) => {
            try {
                logger.info('WebSocket: 收到消息', {
                    socketId: socket.id,
                    current_user: current_user || 'unknown',
                    data
                });
                handleReciveMessage(data);
            } catch (error) {
                logger.info('WebSocket: 处理消息错误', error);
            }
        });

        // 将socket实例保存到ref中
        socketRef.current = socket;
        return socket;
    }, [token, current_user, allowConnect]);

    // 当allowConnect或token变化时，尝试建立连接
    useEffect(() => {
        if (!socketRef.current && allowConnect && token) {
            connectSocket();
        }

        // 在组件卸载时清理连接
        return () => {
            if (socketRef.current) {
                logger.info('WebSocket: 清理连接');
                socketRef.current.disconnect();
                socketRef.current = null;
                setIsConnected(false);
                setConnectionStatus('disconnected');
            }
        };
    }, [allowConnect, token, connectSocket]);

    /**
     * 通过WebSocket发送消息
     * 
     * @param {string} event 要发送的事件名称
     * @param {MessageBase} data 要发送的消息数据
     */
    const message = useCallback((event: string, data: MessageBase) => {
        if (!token) {
            logger.warn('WebSocket: 未找到token，无法发送消息');
            return;
        }

        // 如果当前没有socket实例，尝试重新连接后再发送
        if (!socketRef.current) {
            logger.warn('WebSocket: 未连接，尝试重新连接...');
            const socket = connectSocket();
            if (socket) {
                socket.once('connect', () => {
                    logger.info('WebSocket: 重新连接成功，发送消息');
                    socket.emit(event, data);
                });
            }
            return;
        }

        // 如果当前socket已断开，尝试重连后再发送
        if (!socketRef.current.connected) {
            logger.warn('WebSocket: 连接已断开，尝试重新连接...');
            socketRef.current.connect();
            socketRef.current.once('connect', () => {
                socketRef.current?.emit(event, data);
            });
            return;
        }

        // 在连接正常的情况下发送消息
        try {
            logger.info('WebSocket: 发送消息', {
                event,
                data,
                socketId: socketRef.current.id,
                current_user: current_user || 'unknown'
            });
            socketRef.current.emit(event, data);
        } catch (error) {
            logger.info('WebSocket: 发送消息错误', error);
        }
    }, [token, current_user, connectSocket]);

    return {
        isWsConnected,
        message,
        socket: socketRef.current,
        isModalOpen,
        setIsModalOpen,
        connectionStatus,
        tokenHistory: []
    };
};

/**
 * 默认的消息处理函数
 * @param {any} data 接收到的消息数据
 */
const defaultOnMessage = (data: any) => {
    logger.info('WebSocket: 收到消息', { data });
};
