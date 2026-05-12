import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface UserStore {
  channelName: string | null;
  channelURL: string | null;
  setUser: (channelName: string | null, channelURL: string | null) => void;
  clearUser: () => void;
}

const useUserStore = create<UserStore>()(
  persist(
    set => ({
      channelName: null,
      channelURL: null,
      setUser: (channelName, channelURL) => set({ channelName, channelURL }),
      clearUser: () => set({ channelName: null, channelURL: null }),
    }),
    {
      name: 'user-storage',
    },
  ),
);

export default useUserStore;
