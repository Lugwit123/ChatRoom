import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { UserBaseAndDevices } from '../types/types';

interface UserStore {
  currentSelectedUser: UserBaseAndDevices | null;
  selectUser: (user: UserBaseAndDevices) => void;
  clearSelectedUser: () => void;
  updateUserName: (id: number, name: string) => void;
}

const useCurrentSelectedUserStore = create<UserStore>()(
  devtools(
    (set) => {
      const updateCurrentUser = (user: UserBaseAndDevices | null) =>
        set({ currentSelectedUser: user }, false, 'updateCurrentUser');

      return {
        currentSelectedUser: null,

        selectUser: (user) => updateCurrentUser(user),

        clearSelectedUser: () => updateCurrentUser(null),

        updateUserName: (id, name) =>
          set((state) => {
            const user = state.currentSelectedUser;
            return user && user.id === id
              ? { currentSelectedUser: { ...user, name } }
              : state;
          }, false, 'updateUserName'),
      };
    },
    { name: 'UserStore' }
  )
);

export default useCurrentSelectedUserStore;
