// frontend/src/components/CurrentLoginUserDisplay.tsx
import React, { useState, useEffect } from 'react';
import { UserBaseAndStatus, UserRole,MessageType,MessageContentType,MessageBase } from '../types/types';
import UserAvatar from './UserAvatar';
import Announcement from './Announcement';
import './CurrentLoginUserDisplay.css';
import { logger } from '../utils/logger';
import { useIsLocalEnv } from '../providers/QueryProvider';
import {executeByEnv,exit_app} from '../utils/actions_utils';
import { useNavigate, useLocation } from 'react-router-dom';

interface CurrentLoginUserDisplayProps {
    currentLoginUser: UserBaseAndStatus | null;
    handleLogout: () => void;
    isWsConnected: boolean;
    websocket : any;
}

declare global {
    interface Window {
      QWebChannel: any;
    }
}
const CurrentLoginUserDisplay: React.FC<CurrentLoginUserDisplayProps> = ({ 
    currentLoginUser, 
    handleLogout, 
    isWsConnected,
    websocket
}) => {
    const [showAnnouncement, setShowAnnouncement] = useState<boolean>(false);
    const navigate = useNavigate();
    const location = useLocation();
    logger.info(currentLoginUser)
    // const handleSendMessage = useHandleSendMessage(); // 获取封装的发送消息函数
    const { data: isLocalEnv, isLoading, error } = useIsLocalEnv(); // 启用查询

    const handleAnnouncementClick = () => {
        if (location.pathname === '/announcement') {
            // 如果已经在公告页面，返回上一页
            navigate(-1);
        } else {
            // 否则导航到公告页面
            navigate('/announcement');
        }
    };

    return (
        <>
            <button 
                className={`announcement-button ${location.pathname === '/announcement' ? 'active' : ''}`} 
                onClick={handleAnnouncementClick} 
                aria-label="查看公告"
            >
                公告
            </button>
            {showAnnouncement && <Announcement onClose={() => setShowAnnouncement(false)} isModal={true} />}
            <div style={{ flexGrow: 1 }}></div>
            <div className={`ws-status ${isWsConnected? 'connected' : 'disconnected'}`}>
                {isWsConnected ? '在线' : '离线'}
            </div>
            <div id='sid'>
                { websocket ? websocket.id : 'no sid'}
            </div>
            {isLocalEnv ? "->local" : "->net"}
            <div className="user-info-display">
                <UserAvatar
                    className="current-user-avatar"
                    user={currentLoginUser}
                />
                <span className="user-nickname">
                    {currentLoginUser?.nickname || currentLoginUser?.username}
                </span>
                <button onClick={handleLogout} className="logout-button" aria-label="Logout">
                    登出
                </button>
                {}
                <button onClick={()=>{exit_app()}} id="test" aria-label="Logout">
                    退出
                </button>
            </div>
        </>
    );
};

export default CurrentLoginUserDisplay;
