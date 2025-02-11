// frontend/src/components/ChatApp.tsx
// @ts-nocheck
import React from 'react';
import UserList from './UserList';
import { useChatContext } from '../contexts/rqContext';
import ChatPanel from './ChatPanel';
import './ChatApp.css';
import { useUsersQuery, useGroupsQuery} from '../providers/QueryProvider';
import { logger } from '../utils/logger';

interface ChatAppProps {
    className?: string;
}

const ChatApp: React.FC<ChatAppProps> = ({ className }) => {
    const { data: users, isLoading: isAccountsLoading } = useUsersQuery();
    const { data: groups, isLoading: isGroupsLoading } = useGroupsQuery();

    return (
        
        <>  
            <div className="main-content">
                <UserList
                    users={users}
                    groups={groups}
                />
                <ChatPanel />
            </div>
        </>

    );
}

export default ChatApp;
