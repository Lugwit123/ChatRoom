import React from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';

export interface TokenHistoryEntry {
    token: string;
    timestamp: string;
}

const TOKEN_HISTORY_KEY = 'tokenHistory';

export const useTokenHistory = () => {
    const queryClient = useQueryClient();

    // 获取历史记录
    const { data: tokenHistory = [] } = useQuery<TokenHistoryEntry[]>({
        queryKey: [TOKEN_HISTORY_KEY],
        initialData: []
    });

    // 添加新记录
    const addTokenHistory = (token: string) => {
        const newEntry: TokenHistoryEntry = {
            token,
            timestamp: new Date().toISOString()
        };

        queryClient.setQueryData<TokenHistoryEntry[]>(
            [TOKEN_HISTORY_KEY],
            (old = []) => [...old, newEntry]
        );
    };

    return {
        tokenHistory,
        addTokenHistory
    };
}; 