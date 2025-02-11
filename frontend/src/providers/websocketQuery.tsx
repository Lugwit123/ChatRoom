// useWebSocketQuery.tsx
import { useQuery, useQueryClient, UseQueryOptions } from '@tanstack/react-query';
import { Socket } from 'socket.io-client';
import { useWebSocketConnection } from '../hooks/useWebSocketConnection';
import { MessageBase, UsersInfoDictResponse } from '../types/types';
import { QUERY_KEYS } from './QUERY_KEYS';
import { useEffect, useMemo } from 'react';
import { useMessageReceiver } from '../hooks/useMessageReceiver';
import { logger } from '../utils/logger';
// 定义一个更具体的类型
type WebSocketQueryOptions = Omit<UseQueryOptions<Socket | null, Error>, 'queryKey' | 'queryFn'>;

export const useWebSocketQuery = (allowConnect: boolean = true, options?: WebSocketQueryOptions) => {
    const queryClient = useQueryClient();
    const { MessageReceiver } = useMessageReceiver(null);
    const { socket, isWsConnected } = useWebSocketConnection({
        handleReciveMessage: MessageReceiver, // 错误：键名应为 onMessage
        allowConnect: allowConnect
    });

    logger.info('useWebSocketQuery state:', {
        allowConnect,
        hasSocket: !!socket,
        isWsConnected,
        enabled: allowConnect && !isWsConnected
    });

    const { data, error, isLoading, isError, isSuccess, refetch } = useQuery<Socket | null, Error>({
        queryKey: [QUERY_KEYS.WEBSOCKET],
        queryFn: async () => {
            logger.info('WebSocket queryFn executing');
            if (!socket || !isWsConnected) {
                throw new Error('WebSocket connection failed');
            }
            logger.info('WebSocket 已连接，返回 socket 对象');
            return socket;
        },
        enabled: allowConnect && !isWsConnected,
        staleTime: Infinity,
        retry: 1,
        retryDelay: 1000,
        gcTime: Infinity,
        ...options,
    });

    const cachedSocket = useMemo(() => {
        return isWsConnected ? socket : data;
    }, [isWsConnected, socket, data]);

    useEffect(() => {
        if (allowConnect){
        logger.info('WebSocket connection status changed:', {
            allowConnect,
            hasSocket: !!socket,
            isWsConnected,
            isLoading,
            isError,
            isSuccess,
            cachedSocket: !!cachedSocket
        })};
    }, [allowConnect, socket, isWsConnected, isLoading, isError, isSuccess, cachedSocket]);

    useEffect(() => {
        if (!socket) {
            return;
        }


        socket.on('user_status', (data) => {
            logger.info('用户状态更新:', data);
            // 可以在此更新USERS中的user_map相应用户的status
        });

        socket.on('close', () => {
            logger.info('WebSocket 连接已关闭');
        });

        return () => {
            // socket.off('message', handleMessage);
            socket.off('user_status');
            socket.off('close');
        };
    }, [socket, queryClient]);

    return {
        socket: cachedSocket,
        error,
        isLoading,
        isError,
        isSuccess,
        refetch,
        isWsConnected
    };
};
