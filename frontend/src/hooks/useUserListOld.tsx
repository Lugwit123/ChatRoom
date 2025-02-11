// frontend/src/hooks/useUserList.tsx
// @ts-nocheck
import { useEffect, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getUserList, sendMessage, getChatHistory } from '../services/api';
import { UserBaseAndStatus, AccountsMap, UserRole, UserListResponse } from '../types/types';

interface UseUserListProps {
    apiUrl: string;
    token: string | null;
    currentUser: string | null;
    setAccounts: React.Dispatch<React.SetStateAction<AccountsMap>>;
    setUsers: React.Dispatch<React.SetStateAction<UserBaseAndStatus[]>>;
    setGroups: React.Dispatch<React.SetStateAction<string[]>>;
    setError: React.Dispatch<React.SetStateAction<string | null>>;
}

export function useUserList({
    apiUrl,
    token,
    currentUser,
    setAccounts,
    setUsers,
    setGroups,
    setError,
}: UseUserListProps) {
    const queryClient = useQueryClient();

    // 获取用户列表
    const userListQuery = useQuery<UserListResponse, Error>({
        queryKey: ['userList'],
        queryFn: getUserList,
        enabled: !!token,
        staleTime: 30000, // 30秒内不重新获取
        gcTime: 5 * 60 * 1000, // 5分钟的垃圾回收时间
        refetchInterval: 60000, // 每60秒重新获取一次
        refetchOnWindowFocus: false,
        refetchOnMount: false,
        refetchOnReconnect: false,
    });

    // 使用 useCallback 包装数据处理函数，并添加必要的依赖项
    const processUserListData = useCallback(
        (data: UserListResponse | undefined) => {
            if (!data) return;

            const { users, groups } = data;
            
            // 只在数据有变化时更新
            setUsers(prevUsers => {
                const isEqual =
                    prevUsers.length === users.length &&
                    prevUsers.every((user, index) => user.id === users[index].id && user.role === users[index].role);
                return isEqual ? prevUsers : users;
            });

            setGroups(prevGroups => {
                const groupNames = groups.map(group => group.name);
                const isEqual =
                    prevGroups.length === groupNames.length &&
                    prevGroups.every((name, index) => name === groupNames[index]);
                return isEqual ? prevGroups : groupNames;
            });
        },
        [setUsers, setGroups]
    );

    // 监听数据变化
    useEffect(() => {
        if (userListQuery.data) {
            processUserListData(userListQuery.data);
        }
    }, [userListQuery.data, processUserListData]);

    // 监听错误
    useEffect(() => {
        if (userListQuery.error) {
            setError(userListQuery.error.message || '获取用户列表失败');
        }
    }, [userListQuery.error, setError]);

    // 发送消息
    const sendMessageMutation = useMutation({
        mutationFn: sendMessage,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['messages'] });
        },
    });

    // 创建一个新的 hook 来处理聊天历史
    const chatHistoryQuery = useQuery({
        queryKey: ['messages', currentUser],
        queryFn: () => getChatHistory(currentUser || ''),
        enabled: !!currentUser,
    });

    return {
        userListData: userListQuery.data,
        isLoading: userListQuery.isLoading,
        error: userListQuery.error,
        sendMessage: sendMessageMutation.mutate,
        chatHistory: chatHistoryQuery.data,
        isChatHistoryLoading: chatHistoryQuery.isLoading,
        chatHistoryError: chatHistoryQuery.error,
    };
}
