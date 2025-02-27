// frontend/src/components/CurrentLoginUserDisplay.tsx
import React, { useState, useEffect, useCallback } from 'react';
import { UserBaseAndDevices, UserRole, MessageType, MessageContentType, MessageBase } from '../types/types';
import UserAvatar from './UserAvatar';
import Announcement from './Announcement';
import './CurrentLoginUserDisplay.css';
import { logger } from '../utils/logger';
import { useIsLocalEnv } from '../providers/QueryProvider';
import { executeByEnv, exit_app } from '../utils/actions_utils';
import { useNavigate, useLocation } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';

interface DeviceInfo {
    device_id: string;
    device_type: string;
    last_seen: string;
    ip_address?: string;
    user_agent?: string;
}

interface OnlineStatus {
    isOnline: boolean;
    devices: DeviceInfo[];
}

interface CurrentLoginUserDisplayProps {
    currentLoginUser: UserBaseAndDevices | null;
    handleLogout: () => void;
    isWsConnected: boolean;
    websocket: any;
}

const CurrentLoginUserDisplay: React.FC<CurrentLoginUserDisplayProps> = ({ 
    currentLoginUser, 
    handleLogout, 
    isWsConnected,
    websocket
}) => {
    const [showAnnouncement, setShowAnnouncement] = useState<boolean>(false);
    const [localWsStatus, setLocalWsStatus] = useState<boolean>(isWsConnected);
    const navigate = useNavigate();
    const location = useLocation();
    const { data: isLocalEnv } = useIsLocalEnv();

    // 使用React Query检查设备状态
    const { data: deviceStatus } = useQuery<OnlineStatus>({
        queryKey: ['deviceStatus', currentLoginUser?.username],
        queryFn: async () => {
            try {
                const response = await fetch(`/api/users/${currentLoginUser?.username}/devices`, {
                    method: 'GET',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'include'
                });
                
                if (!response.ok) {
                    throw new Error('Failed to fetch device status');
                }
                
                const data = await response.json();
                return {
                    isOnline: data.devices.length > 0,
                    devices: data.devices
                };
            } catch (error) {
                logger.error('Failed to check device status:', error);
                return {
                    isOnline: false,
                    devices: []
                };
            }
        },
        refetchInterval: 10000,
        enabled: !!currentLoginUser?.username
    });

    useEffect(() => {
        if (!isWsConnected && localWsStatus) {
            setLocalWsStatus(false);
            // 当WebSocket断开时，尝试清理设备状态
            if (websocket?.id && currentLoginUser?.username) {
                fetch(`/api/users/${currentLoginUser.username}/devices/${websocket.id}`, {
                    method: 'DELETE',
                    credentials: 'include',
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem('token')}`
                    }
                }).catch(error => {
                    logger.error('清理设备状态失败:', error);
                });
            }
        } else if (isWsConnected && !localWsStatus) {
            setLocalWsStatus(true);
            // 当WebSocket连接时，更新设备状态
            if (websocket?.id && currentLoginUser?.username) {
                const deviceInfo = {
                    device_type: 'web',
                    ip_address: '',
                    user_agent: navigator.userAgent,
                    device_id: websocket.id
                };
                fetch(`/api/users/${currentLoginUser.username}/devices/${websocket.id}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${localStorage.getItem('token')}`
                    },
                    credentials: 'include',
                    body: JSON.stringify(deviceInfo)
                }).catch(error => {
                    logger.error('更新设备状态失败:', error);
                });
            }
        }
    }, [isWsConnected, localWsStatus, currentLoginUser?.username, websocket?.id]);

    // 获取状态显示文本
    const getStatusText = () => {
        if (!localWsStatus) return '离线';
        if (!deviceStatus) return '连接中...';
        
        const deviceCount = deviceStatus.devices.length;
        if (deviceCount === 0) return '离线';
        if (deviceCount === 1) return '在线';
        return `在线(${deviceCount}个设备)`;
    };

    // 获取设备列表提示文本
    const getDeviceTooltip = () => {
        if (!deviceStatus?.devices.length) return '当前没有在线设备';
        
        return deviceStatus.devices.map(device => {
            const lastSeen = new Date(device.last_seen).toLocaleString();
            return `${device.device_type}${device.device_id === websocket?.id ? '(当前设备)' : ''}\n最后在线: ${lastSeen}`;
        }).join('\n');
    };

    const handleAnnouncementClick = () => {
        if (location.pathname === '/announcement') {
            navigate(-1);
        } else {
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
            <div 
                className={`ws-status ${localWsStatus ? 'connected' : 'disconnected'}`}
                title={getDeviceTooltip()}
            >
                {getStatusText()}
            </div>
            <div id='sid' title="设备ID">
                {websocket?.id || 'no sid'}
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
                <button onClick={()=>{exit_app()}} id="test" aria-label="Logout">
                    退出
                </button>
            </div>
        </>
    );
};

export default CurrentLoginUserDisplay;
