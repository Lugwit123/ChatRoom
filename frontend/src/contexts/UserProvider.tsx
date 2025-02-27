import React, { createContext, useContext, useState, useCallback, ReactNode, useEffect } from 'react';
import { UserBaseAndDevices, UserRole } from '../types/types';
import { loginUser } from '../services/api';

export interface UserContextType {
    token: string | null;
    current_user: string | null;
    users: UserBaseAndDevices[];
    loading: boolean;
    error: string | null;
    login: (username: string, password: string) => Promise<void>;
    logout: () => void;
    updateUsers: (newUsers: UserBaseAndDevices[]) => void;
}

export const UserContext = createContext<UserContextType | null>(null);

export const useUsers = () => {
    const context = useContext(UserContext);
    if (!context) {
        throw new Error('useUsers must be used within a UserProvider');
    }
    return context;
};

export const UserProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
    const [token, setToken] = useState<string | null>(null);
    const [current_user, setCurrentUser] = useState<string | null>(null);
    const [users, setUsers] = useState<UserBaseAndDevices[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Token 本地存储
    useEffect(() => {
        const storedToken = localStorage.getItem('token');
        if (storedToken) {
            setToken(storedToken);
        }
    }, []);

    useEffect(() => {
        if (token) {
            localStorage.setItem('token', token);
        } else {
            localStorage.removeItem('token');
        }
    }, [token]);

    const login = useCallback(async (username: string, password: string) => {
        setLoading(true);
        setError(null);
        try {
            const response = await loginUser(username, password);
            setToken(response.access_token);
            setCurrentUser(username);
            
            // 创建初始用户对象
            const newUserAccount: UserBaseAndDevices = {
                username,
                nickname: username,
                online: true,
                role: UserRole.user,
                id: 0,
                status: 'online',
                unread_message_count: 0,
                messages: [],
                avatar_index: 2
            };

            setUsers(prev => [...prev, newUserAccount]);
        } catch (err) {
            setError(err instanceof Error ? err.message : '登录失败');
        } finally {
            setLoading(false);
        }
    }, []);

    const logout = useCallback(() => {
        setToken(null);
        setCurrentUser(null);
        setUsers([]);
    }, []);

    const updateUsers = useCallback((newUsers: UserBaseAndDevices[]) => {
        setUsers(newUsers);
    }, []);

    const contextValue: UserContextType = {
        token,
        current_user,
        users,
        loading,
        error,
        login,
        logout,
        updateUsers
    };

    return (
        <UserContext.Provider value={contextValue}>
            {children}
        </UserContext.Provider>
    );
}; 