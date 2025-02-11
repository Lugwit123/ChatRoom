// frontend/src/utils/getAvatarIndex.ts

export const get_avatar_index = (username: string = ""): number => {
    if (typeof username !== 'string') {
        return 1; // 返回默认头像索引
    }

    let hash = 0;
    for (let i = 0; i < username.length; i++) {
        hash = username.charCodeAt(i) + ((hash << 5) - hash);
    }
    return Math.abs(hash) % 5 + 1; // 假设有5个头像
};
