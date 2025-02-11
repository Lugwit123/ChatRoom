// UserAvatar.tsx

import React from 'react';
import { UserBaseAndStatus } from '../types/types';

interface UserAvatarProps {
    user: UserBaseAndStatus;
    className?: string; // 允许传入自定义类名
}

const UserAvatar: React.FC<UserAvatarProps> = ({ user, className }) => {
    const avatar_index = user?.avatar_index || 2; // 默认值为2
    const avatarUrl = `/avatars/avatar${avatar_index}.png`;

    return (
        <img
            src={avatarUrl}
            alt={`${user?.nickname || user?.username} 的头像`}
            className={`${className} user-avatar ${user?.online ? 'online' : 'offline'}`} // 动态添加传入的类名
        />
    );
};

export default UserAvatar;
