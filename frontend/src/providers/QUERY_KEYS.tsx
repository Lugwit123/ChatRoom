
// queryKeys.ts
export const QUERY_KEYS = {
    CURRENTLOGINUSER: 'current_login_user',
    USERS: 'users',
    CONVERSATIONS: 'conversations',
    GROUPS: 'groups',
    WEBSOCKET: 'websocket',
    TOKEN: 'token',
    MESSAGES: {
        LIST: 'messages',
        BY_USER: (userId: number) => ['messages', userId] as const,
    },
    ISPYWEBVIEW:'pywebview'
};
