import React, { createContext, useContext } from 'react';
import { Socket } from 'socket.io-client';


const ChatContext = createContext<{
    users: any;
    groups: any;
    socket: Socket | null;
    isWsConnected: boolean;
} | null>(null);

export const useChatContext = () => {
    const context = useContext(ChatContext);
    if (!context) {
        throw new Error('useChatContext must be used within a ChatProvider');
    }
    return context;
};

export const ChatProvider: React.FC<{
    users: any;
    groups: any;
    socket: Socket | null;
    isWsConnected: boolean;
    children: React.ReactNode;
}> = ({ users, groups, socket, isWsConnected, children }) => {
    return (
        <ChatContext.Provider value={{ users, groups, socket, isWsConnected }}>
            {children}
        </ChatContext.Provider>
    );
};