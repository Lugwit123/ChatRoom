// App.tsx
import React, { useState, useMemo, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, useLocation, useNavigate } from 'react-router-dom';
import AccountForm from './components/AccountForm'; // 登录/注册表单组件
import { useAuth } from './hooks/useAuth';          // 自定义认证Hook
import CurrentLoginUserDisplay from './components/CurrentLoginUserDisplay'; // 显示当前登录用户信息的组件
import ChatApp from './components/ChatApp';         // 聊天主界面组件
import { ChatProvider } from './contexts/rqContext';// 聊天上下文Provider
import { logger } from './utils/logger';
import { useIsLocalEnv } from './providers/QueryProvider';
// 从react-query获取数据的Provider模块
import {
    useUsersQuery,
    useGroupsQuery,
    QueryProvider,
    useWebSocketQuery,
    useToken
} from './providers/QueryProvider';

import './App.css'; // CSS样式文件

import Announcement from './components/Announcement';
import Lantern from './components/Lantern/Lantern'; // 导入Lantern组件

const Login = React.memo(() => {
    const { isAuthenticated, currentLoginUser, handleAuthSubmit, logout } = useAuth();
    const [mode, setMode] = useState<'login' | 'register'>('login');

    return (
        <div className="login-container">
            {!isAuthenticated ? (
                <AccountForm
                    onSubmit={handleAuthSubmit}
                    mode={mode}
                    setMode={setMode}
                />
            ) : (
                <AppContent />
            )}
        </div>
    );
});

Login.displayName = 'Login';

const AppContent = React.memo(() => {
    const { data: users, isLoading: isAccountsLoading } = useUsersQuery();
    
    const allowConnect = !isAccountsLoading && !!users?.current_user;
    
    const { socket, isWsConnected } = useWebSocketQuery(allowConnect, {
        retry: false,
        enabled: allowConnect
    });

    const { isAuthenticated, currentLoginUser, handleAuthSubmit, logout } = useAuth();
    const current_user = users?.current_user;
    const { data: isLocalEnv, isLoading, error } = useIsLocalEnv(); // 获取更多状态信息
    useEffect(() => {
        const initializeQWebChannel = async () => {
            console.log('环境状态:', {
                isLocalEnv,
                isLoading,
                error
            });
            if (isLocalEnv !== undefined) {  // 确保有值
                console.log('当前环境:', isLocalEnv);
                // 创建 script 元素加载 QWebChannel 脚本
                const script = document.createElement("script");
                script.src = "qwebchannel.js"; // 确保路径正确，PyWebView 环境提供此文件
                script.onload = () => {
                    const qt = (window as any).qt; // Qt 提供的 webChannelTransport
                    if (qt && (window as any).QWebChannel) {
                        new (window as any).QWebChannel(qt.webChannelTransport, (channel: any) => {
                            // 将 Python 提供的对象暴露到全局 window
                            (window as any).pyObj = channel.objects.pyObj;


                        });
                    } else {
                        console.error("QWebChannel 或 qt 未加载");
                    }
                };
                script.onerror = () => {
                    console.error("无法加载 QWebChannel 脚本，请检查路径");
                };

                document.head.appendChild(script);
            } else {
                console.log("未检测到 PyWebView 环境");
            }
        };

        initializeQWebChannel();
    }, [isLocalEnv]);
        
    return (
        <div className="app-container">
            <header style={{ padding: 0, top: 0, margin: 0 }}>
                <div className="CurrentLoginUserDisplay">
                    <CurrentLoginUserDisplay
                        currentLoginUser={current_user}
                        handleLogout={logout}
                        isWsConnected={isWsConnected}
                        websocket={socket}
                    />
                </div>
            </header>
            {isWsConnected && <ChatApp className="ChatApp" />}
            <Lantern /> // 使用Lantern组件
        </div>
    );
});

AppContent.displayName = 'AppContent';

// 创建一个包装组件来处理公告页面的显示
const AnnouncementWrapper = () => {
    return (
        <div className="announcement-page">
            <Announcement />
        </div>
    );
};

/**
 * 主App组件
 * 
 * 功能:
 * - 提供QueryProvider上下文支持
 * - 通过AppContent渲染核心逻辑与UI
 */
function App() {
    const { isAuthenticated } = useAuth();
    logger.info("isAuthenticated", {isAuthenticated});

    return (
        <QueryProvider>
            <Router>
                <Routes>
                    <Route path="/" element={<Login />} />
                    <Route path="/announcement" element={<AnnouncementWrapper />} />
                </Routes>
            </Router>
        </QueryProvider>
    );
}

export default App;
