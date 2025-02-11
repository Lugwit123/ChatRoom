// frontend\src\providers\QueryProvider.tsx
import React from 'react';
import { 
    QueryClient, 
    QueryClientProvider
} from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { useGroupsQuery,useToken,useUsersQuery,invalidateMessagesQuery,useIsLocalEnv } from './queries';  // 移除 .tsx 扩展名
import { useWebSocketQuery, } from './websocketQuery';



// 创建 QueryClient 实例，配置全局默认选项
const queryClient = new QueryClient({
    defaultOptions: {
        queries: {
            refetchOnWindowFocus: false,  // 窗口获得焦点时不自动重新获取数据
            retry: 1,                     // 请求失败时重试1次
            staleTime: 1000 * 60 * 5,    // 数据5分钟内被认为是新鲜的，不会重新获取
        },
    },
});



// QueryProvider 组件包装整个应用，提供 React Query 上下文
export const QueryProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    return (
        <QueryClientProvider client={queryClient}>
            {children}
            <ReactQueryDevtools initialIsOpen={false} /> {/* 开发工具，方便调试 */}
        </QueryClientProvider>
    );
};

// 导出查询 hooks
export {
    useGroupsQuery,
    useWebSocketQuery,
    useToken,
    useUsersQuery,
    invalidateMessagesQuery,
    useIsLocalEnv
};
