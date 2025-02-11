// frontend/src/contexts/GroupContext.tsx

import React, { createContext, useContext, ReactNode } from 'react';

interface Group {
  id: number;
  name: string;
  // 其他群组属性...
}

interface GroupContextProps {
  groups: Group[];
  getGroupMembers: (groupId: number) => Promise<any>;
}

const GroupContext = createContext<GroupContextProps>({
  groups: [],
  getGroupMembers: async () => [],
});

interface GroupProviderProps {
  children: ReactNode;
}

export function GroupProvider({ children }: GroupProviderProps) {
  // 实现 provider 逻辑...
  
  return (
    <GroupContext.Provider value={{
      groups: [], // 实际的群组数据
      getGroupMembers: async (groupId) => {
        // 实现获取群组成员的逻辑
      }
    }}>
      {children}
    </GroupContext.Provider>
  );
}

export const useGroup = () => useContext(GroupContext);
