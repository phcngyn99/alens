/**
 * Authentication hook and store using Zustand.
 */
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { auth } from '../services/api';
import type { UserRole } from '../types';

interface AuthState {
  token: string | null;
  username: string | null;
  role: UserRole | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (username: string, password: string) => Promise<boolean>;
  logout: () => void;
  clearError: () => void;
  isAdmin: () => boolean;
}

export const useAuth = create<AuthState>()(
  persist(
    (set, get) => ({
      token: null,
      username: null,
      role: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      login: async (username: string, password: string) => {
        set({ isLoading: true, error: null });
        try {
          const response = await auth.login(username, password);
          localStorage.setItem('token', response.access_token);
          set({
            token: response.access_token,
            username: response.username,
            role: response.role,
            isAuthenticated: true,
            isLoading: false,
          });
          return true;
        } catch (error: unknown) {
          const message = error instanceof Error ? error.message : 'Login failed';
          set({
            error: message,
            isLoading: false,
          });
          return false;
        }
      },

      logout: () => {
        localStorage.removeItem('token');
        set({
          token: null,
          username: null,
          role: null,
          isAuthenticated: false,
        });
      },

      clearError: () => set({ error: null }),

      isAdmin: () => get().role === 'admin',
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        token: state.token,
        username: state.username,
        role: state.role,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);

