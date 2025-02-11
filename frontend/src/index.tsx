import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import './index.css';
// import whyDidYouRender from '@welldone-software/why-did-you-render';
// whyDidYouRender(React);

// 创建QueryClient实例
const queryClient = new QueryClient();

// 使用QueryClientProvider包裹App组件
ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
    <QueryClientProvider client={queryClient}>
            <App />
    </QueryClientProvider>
);
