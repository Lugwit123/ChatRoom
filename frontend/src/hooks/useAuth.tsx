// frontend\src\hooks\useAuth.tsx
import React, { useState, useCallback,useContext } from 'react';
import { loginUser, registerUser } from '../services/api';
import { useTokenHistory } from '../services/tokenHistory';
import { UserLoginRequest, UserRegistrationRequest,CurrentLoginUser } from '../types/types';


interface AuthState {
    isAuthenticated: boolean;
    handleAuthSubmit: (data: UserLoginRequest | UserRegistrationRequest) => Promise<void>;
    logout: () => void;
    error: string | null;
    currentLoginUser:CurrentLoginUser
}

export const useAuth = (): AuthState => {
    const [isAuthenticated, setIsAuthenticated] = useState<boolean>(!!localStorage.getItem('token'));
    const [user, setUser] = useState<{username?: string; token?: string}>({
        username: localStorage.getItem('username') || undefined,
        token: localStorage.getItem('token') || undefined
    });
    const [error, setError] = useState<string | null>(null);
    const { addTokenHistory } = useTokenHistory();
    
    const handleAuthSubmit = useCallback(async (data: UserLoginRequest | UserRegistrationRequest) => {
        try {
            setError(null);
            if (data.mode === 'login') {
                const authResponse = await loginUser(data.username, data.password);
                if (authResponse.access_token) {
                    localStorage.setItem('token', authResponse.access_token);
                    localStorage.setItem('username', data.username);
                    localStorage.setItem('current_username', data.username);
                    
                    setIsAuthenticated(true);
                    setUser({
                        username: data.username,
                        token: authResponse.access_token
                    });
                    
                    addTokenHistory(authResponse.access_token);
                }
            } else if (data.mode === 'register') {
                // 调用注册API
                const registerResponse = await registerUser(data);
                if (registerResponse.success) {
                    // 注册成功后自动登录
                    const authResponse = await loginUser(data.username, data.password);
                    if (authResponse.access_token) {
                        localStorage.setItem('token', authResponse.access_token);
                        localStorage.setItem('username', data.username);
                        localStorage.setItem('current_username', data.username);
                        
                        setIsAuthenticated(true);
                        setUser({
                            username: data.username,
                            token: authResponse.access_token
                        });
                        
                        addTokenHistory(authResponse.access_token);
                    }
                }
            }
        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : '操作失败';
            setError(errorMessage);
            setIsAuthenticated(false);
            localStorage.removeItem('token');
            localStorage.removeItem('username');
        }
    }, [addTokenHistory]);

    const logout = useCallback(() => {
        localStorage.removeItem('token');
        localStorage.removeItem('username');
        setIsAuthenticated(false);
        setUser({
            username: undefined,
            token: undefined
        });
        setError(null);
    }, []);
    const currentLoginUser = {username:user.username}
    return {
        isAuthenticated,
        currentLoginUser,
        handleAuthSubmit,
        logout,
        error
    };
};
