// frontend/src/components/AccountForm.tsx
/* eslint-disable */
import React, { useState, useEffect } from 'react';
import { UserLoginRequest, UserRegistrationRequest, UserRole, EmailStr } from '../types/types';
import './AccountForm.css';
import { logger } from '../utils/logger';
interface AccountFormProps {
    onSubmit: (data: UserLoginRequest | UserRegistrationRequest) => Promise<void>;
    mode: 'login' | 'register';
    setMode: (mode: 'login' | 'register') => void;
}

const AccountForm: React.FC<AccountFormProps> = ({ onSubmit, mode, setMode }) => {
    const [formData, setFormData] = useState({
        username: '',
        nickname: '',
        password: '',
        email: '',
        age: '',
    });
    const [showPassword, setShowPassword] = useState(false); // 控制密码可见性的状态

    // 固定生成用户名、昵称和密码
    const handleGenerateRandomCredentials = () => {
        const username = `user_${Math.floor(Math.random() * 1000)}`;
        setFormData(prev => ({
            ...prev,
            username: username, // 随机用户名
            nickname: `昵称_${username}`, // 随机昵称
            password: 'fqq666', // 固定密码
            email: `${username}@example.com`, // 随机邮箱
        }));
    };

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    // 在组件中进行数据区分
    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();

        if (mode === 'login') {
            const loginData: UserLoginRequest = {
                username: formData.username,
                password: formData.password,
                mode: 'login',
            };
            logger.info('Login Data:', loginData);
            onSubmit(loginData);
        } else {
            const registerData: UserRegistrationRequest = {
                username: formData.username,
                password: formData.password,
                nickname: formData.nickname,
                email: formData.email as EmailStr,
                age: formData.age ? parseInt(formData.age, 10) : undefined,
                mode: 'register',
                role: UserRole.user,
            };
            logger.info('Register Data:', registerData);
            onSubmit(registerData);
        }
    };

    // 使用 useEffect 将 setFormData 暴露到 window
    useEffect(() => {
        // 为了避免 TypeScript 报错，需要扩展 Window 接口
        (window as any).setFormData = setFormData;

        // 可选：也可以暴露 formData 本身
        (window as any).formData = formData;

        // 清理函数：组件卸载时移除绑定
        return () => {
            delete (window as any).setFormData;
            delete (window as any).formData;
        };
    }, [setFormData, formData]); // 依赖项包含 setFormData 和 formData

    return (
        <form onSubmit={handleSubmit} className="account-form">
            <h2>{mode === 'login' ? '登录' : '注册'}</h2>
            {mode === 'register' && (
                <div className="form-group">
                    <label>昵称</label>
                    <input
                        type="text"
                        name="nickname"
                        value={formData.nickname}
                        onChange={handleChange}
                        required
                    />
                </div>
            )}
            <div className="form-group">
                <label>用户名</label>
                <input
                    className="form-input"
                    type="text"
                    name="username"
                    value={formData.username}
                    onChange={handleChange}
                    required
                />
            </div>
            <div className="form-group password-group">
                <label>密码</label>
                <div className="password-input-container">
                    <input
                        className="form-input"
                        type={showPassword ? 'text' : 'password'} // 根据状态切换输入框类型
                        name="password"
                        value={formData.password}
                        onChange={handleChange}
                        required
                    />
                    <span
                        className="password-toggle"
                        onClick={() => setShowPassword(!showPassword)} // 切换密码可见性
                    >
                        {showPassword ? '👁️' : '👁️‍🗨️'} {/* 切换小眼睛图标 */}
                    </span>
                </div>
            </div>
            {mode === 'register' && (
                <>
                    <div className="form-group">
                        <label>邮箱</label>
                        <input
                            type="email"
                            name="email"
                            value={formData.email}
                            onChange={handleChange}
                            required
                        />
                    </div>
                    <div className="form-group">
                        <label>年龄</label>
                        <input
                            type="number"
                            name="age"
                            value={formData.age}
                            onChange={handleChange}
                        />
                    </div>
                </>
            )}
            <button type="submit" className="submit-button">
                {mode === 'login' ? '登录' : '注册'}
            </button>
            {/* 只在注册模式下显示生成按钮 */}
            {mode === 'register' && (
                <button
                    type="button"
                    className="generate-button"
                    onClick={handleGenerateRandomCredentials}
                >
                    随机生成用户名、昵称、密码和邮箱
                </button>
            )}
            <div className="toggle-mode">
                {mode === 'login' ? (
                    <button type="button" onClick={() => setMode('register')}>注册</button>
                ) : (
                    <button type="button" onClick={() => setMode('login')}>返回登录</button>
                )}
            </div>
        </form>
    );
};

export default AccountForm;
