import { defineStore } from 'pinia';

import api from '@/lib/http';

interface LoginPayload {
  email: string;
  password: string;
}

interface TokenResponse {
  access_token: string;
  token_type: string;
  user_id: number;
  roles: string[];
  display_name?: string | null;
}

const STORAGE_KEY = 'campuswap_token';

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem(STORAGE_KEY) ?? '',
    userId: null as number | null,
    roles: [] as string[],
    displayName: '',
    loading: false,
    error: '',
    lastLoginAt: ''
  }),
  getters: {
    isAuthenticated: (state) => Boolean(state.token),
    isAdmin: (state) => state.roles.includes('market_admin')
  },
  actions: {
    async login(payload: LoginPayload) {
      this.loading = true;
      this.error = '';
      try {
        const { data } = await api.post<TokenResponse>('/auth/login', payload);
        this.token = data.access_token;
        this.lastLoginAt = new Date().toISOString();
        this.userId = data.user_id;
        this.roles = data.roles;
        this.displayName = data.display_name ?? '';
        localStorage.setItem(STORAGE_KEY, data.access_token);
      } catch (error) {
        this.error = (error as Error).message;
        throw error;
      } finally {
        this.loading = false;
      }
    },
    async fetchProfile() {
      if (!this.token) return;
      try {
        const { data } = await api.get<TokenResponse>('/auth/me');
        this.token = data.access_token;
        this.userId = data.user_id;
        this.roles = data.roles;
        this.displayName = data.display_name ?? '';
        localStorage.setItem(STORAGE_KEY, data.access_token);
      } catch (error) {
        console.warn('[auth] failed to refresh profile', error);
      }
    },
    logout() {
      this.token = '';
      this.userId = null;
      this.roles = [];
      this.displayName = '';
      this.lastLoginAt = '';
      localStorage.removeItem(STORAGE_KEY);
    }
  }
});
