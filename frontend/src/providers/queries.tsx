import { useQuery,QueryClient } from '@tanstack/react-query';
import {  Group, CurrentLoginUser, UserBaseAndStatus, UsersInfoDictResponse } from '../types/types';
import { getGroups, getUserInfoDict } from '../services/api';
import { QUERY_KEYS } from './QUERY_KEYS';
import useGlobalState from "../stores/useGlobalState";
import { logger } from '../utils/logger';
// 用于获取用户列表的 hook
// export const useUsersQuery = () => {
//     logger.info("useUsersQuery")
//     return useQuery<UsersInfoDictResponse>({
//         queryKey: [QUERY_KEYS.USERS],
//         queryFn: async () => {
//             const response = await getUserInfoDict();
//             // 确保返回的是数组
//             logger.info('useUsers response:', response);
//             return Array.isArray(response) ? response : response;
//         },
//         staleTime: 1000 * 60 * 5, // 5分钟
//         gcTime: 1000 * 60 * 10,
//     });
// };

export const useUsersQuery = (enabled = true) => {
    logger.info("进入useUsersQuery")
    const shouldRefetch = useGlobalState((state) => state.shouldRefetchUsers);
    const setShouldRefetchUsers = useGlobalState((state) => state.setShouldRefetchUsers);
    return useQuery<UsersInfoDictResponse>({
        queryKey: [QUERY_KEYS.USERS],
        queryFn: async () => {
            logger.info("获取新的数据")
            const response = await getUserInfoDict();
            setShouldRefetchUsers(false);
            return response;
        },
        staleTime: 0, // 5 分钟
        gcTime: 1000 * 60 * 10, // 10 分钟
        enabled:shouldRefetch // 控制是否激活

    });
};

export const useIsLocalEnv = () => {
    logger.info("进入useIsPywebview")
    return useQuery<any>({
        queryKey: [QUERY_KEYS.ISPYWEBVIEW],
        queryFn: async () => {
            console.log(navigator.userAgent,navigator.userAgent.includes("Qt"))
            return navigator.userAgent.includes("Qt");
        },
        enabled:true // 控制是否激活

    });
};


export const invalidateMessagesQuery = (queryClient: QueryClient, data: { sender: string }) => {
    queryClient.invalidateQueries({
        predicate: (query) => {
            const queryKey = query.queryKey;
            const keys = ["users", "user_map", data.sender, "messages"];

            // 如果长度不够，无法匹配
            if (queryKey.length < keys.length) return false;

            // 匹配前几层key是否和 keys 一致
            return keys.every((key, index) => queryKey[index] === key);
        },
    });
};


// invalidateNestedQuery(queryClient, [
//     "users",          // 第一层键
//     "user_map",        // 第二层键
//     data.sender, // 第三层键，比如用户 "john_doe"
//     "messages",       // 第四层键
// ]);
export const useToken = () => {
    return useQuery<string>({
        queryKey: [QUERY_KEYS.TOKEN],
        queryFn: async () => {
            const response =localStorage.getItem('token');
            return response;
        },
        staleTime: 1000 * 60 * 5, // 5分钟
        gcTime: 1000 * 60 * 10,
    });
};



// 用于访问 groups 数据的 hook
export const useGroupsQuery = () => {
    return useQuery<Group[]>({
        queryKey: [QUERY_KEYS.GROUPS],
        queryFn: getGroups,
        staleTime: 1000 * 60 * 5,
        gcTime: 1000 * 60 * 10,
    });
};