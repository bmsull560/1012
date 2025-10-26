import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

interface User {
  id: string;
  email: string;
  name?: string;
  firstName?: string;
  lastName?: string;
  first_name?: string;
  last_name?: string;
  role?: 'admin' | 'analyst' | 'sales' | 'csm' | 'viewer';
  expertiseLevel: 'beginner' | 'intermediate' | 'expert';
  preferences: {
    theme: 'light' | 'dark' | 'system';
    dataGranularity: 'summary' | 'detailed' | 'custom';
    showFormulas: boolean;
    enableNotifications: boolean;
  };
}

interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  token: string | null;
  refreshToken: string | null;
  isLoading?: boolean;
  error?: string | null;
  
  // Actions
  login: (user: User, token: string, refreshToken: string) => void;
  register: (user: User, token: string, refreshToken: string) => void;
  logout: () => void;
  updateUser: (updates: Partial<User>) => void;
  setToken: (token: string) => void;
}

export const useAuthStore = create<AuthState>()(
  devtools(
    persist(
      (set) => ({
        // Initial state
        isAuthenticated: false,
        user: null,
        token: null,
        refreshToken: null,
        isLoading: false,
        error: null,
        
        // Actions
        login: (user, token, refreshToken) => set({
          isAuthenticated: true,
          user,
          token,
          refreshToken,
          isLoading: false,
          error: null,
        }),
        
        register: (user, token, refreshToken) => set({
          isAuthenticated: true,
          user,
          token,
          refreshToken,
          isLoading: false,
          error: null,
        }),
        
        logout: () => set({
          isAuthenticated: false,
          user: null,
          token: null,
          refreshToken: null,
        }),
        
        updateUser: (updates) => set((state) => ({
          user: state.user ? { ...state.user, ...updates } : null,
        })),
        
        setToken: (token) => set({ token }),
      }),
      {
        name: 'auth-storage',
        partialize: (state) => ({
          isAuthenticated: state.isAuthenticated,
          user: state.user,
          token: state.token,
          refreshToken: state.refreshToken,
        }),
      }
    )
  )
);
