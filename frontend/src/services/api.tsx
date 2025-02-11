import axios from 'axios'
import { UserListResponse, MessageBase, 
    Group,MessageType, MessageContentType, 
    AuthResponse, UsersInfoDictResponse,
    UserRegistrationRequest
} from '../types/types'
import { logger } from '../utils/logger';
import { useState } from 'react';

// API基础配置
export const apiUrl = import.meta.env.VITE_API_URL;

export const api = axios.create({
    baseURL: apiUrl,
    timeout: 10000,
    headers: {
        'Content-Type': 'application/json'
    }
});

// 添加请求拦截器，检查 token 和处理未授权情况
api.interceptors.request.use(
    config => {
        const token = localStorage.getItem('token');
        
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        } else {
            // 如果没有 token，可以选择抛出错误或重定向到登录页
            console.warn('No token found. Please login first.');
            // 可以在这里触发登录流程，但需要谨慎处理
        }
        
        return config;
    },
    error => {
        return Promise.reject(error);
    }
);

// 添加响应拦截器，处理 401 未授权错误
api.interceptors.response.use(
    response => response,
    error => {
        if (error.response && error.response.status === 401) {
            // token 过期或无效，清除 token 并重定向到登录页
            localStorage.removeItem('token');
            console.error('Token 无效，请重新登录');
            
            // 如果有全局的错误处理或路由，可以在这里触发
            // 例如：window.location.href = '/login';
        }
        return Promise.reject(error);
    }
);

// 用户相关API
export const getUserInfoDict = async (): Promise<UsersInfoDictResponse> => {
    try {
        logger.info('正在获取用户列表...');
        logger.info('当前token:', localStorage.getItem('token'));
        
        const { data } = await api.get('/api/users_map');
        logger.info('获取用户列表成功:', data);
        return data;
    } catch (error) {
        if (axios.isAxiosError(error)) {
            if (error.response?.status === 401) {
                console.error('认证失败，请重新登录');
                localStorage.removeItem('token');
            }
            throw new Error(error.response?.data?.detail || '获取用户列表失败');
        }
        console.error('获取用户列表失败:', error);
        throw error;
    }
};

export const getGroups = async (): Promise<Group[]> => {
    try {
        const { data } = await api.get<Group[]>('/api/groups');
        logger.info('获取群组列表成功:', data);
        return data;
    } catch (error) {
        console.error('获取群组列表失败:', error);
        throw error;
    }
};

export const getGroupMembers = async (groupId: number) => {
    const { data } = await api.get(`/api/groups/${groupId}/members`);
    return data;
};

export const loginUser = async (username: string, password: string): Promise<AuthResponse> => {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);
    
    try {
        const response = await api.post('/api/login', formData, {
            headers: {
                'Content-Type': 'multipart/form-data'
            }
        });

        const authResponse: AuthResponse = {
            access_token: response.data.access_token,
            token_type: response.data.token_type,
            token: response.data.token,
            detail: response.data.detail || '登录成功'
        };

        if (authResponse.access_token) {
            localStorage.setItem('token', authResponse.access_token);
            logger.info('登录成功，Token已保存:', authResponse.access_token);
        } else {
            throw new Error('未收到有效的访问令牌');
        }

        return authResponse;
    } catch (error) {
        if (axios.isAxiosError(error)) {
            if (error.response?.status === 401) {
                console.error('认证失败：用户名或密码错误');
                throw new Error('用户名或密码错误');
            } else if (error.response?.status === 422) {
                console.error('请求参数验证失败');
                throw new Error('请求参数无效');
            } else {
                console.error('登录失败:', error.response?.data || error.message);
                throw new Error(error.response?.data?.detail || '登录失败，请稍后重试');
            }
        }
        console.error('登录发生未知错误:', error);
        throw error;
    }
};

// WebSocket相关配置
export const SOCKET_CONFIG = {
    reconnection: true,
    reconnectionAttempts: 5,
    reconnectionDelay: 1000,
    reconnectionDelayMax: 5000,
    timeout: 20000,
    autoConnect: true,
    transports: ['websocket'],
    path: '/socket.io/',
    extraHeaders: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
    }
};

// 消息发送相关
export interface SendMessageServerParams {
    message: string;
    recipient: string;
    sender: string;
    sendMessageFn: (event: string, payload: MessageBase) => void;
    recipientType: 'group' | 'private';
    groupNames?: string[];
    messageType: MessageType;
    contentType: MessageContentType;
}


export const registerUser = async (data: UserRegistrationRequest) => {
    const response = await fetch(`${apiUrl}/register`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
    });

    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || '注册失败');
    }

    return await response.json();
}; 