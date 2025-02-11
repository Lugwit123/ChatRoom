import { create } from "zustand";

/**
 * 定义全局状态，用于控制是否需要刷新特定数据
 */
interface GlobalState {
    shouldRefetchUsers: boolean;
    setShouldRefetchUsers: (value: boolean) => void;
}

const useGlobalState = create<GlobalState>((set) => ({
    shouldRefetchUsers: true,
    setShouldRefetchUsers: (value) => set({ shouldRefetchUsers: value }),
}));

export default useGlobalState;

