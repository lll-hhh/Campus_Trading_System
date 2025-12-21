import { defineStore } from 'pinia';

import  { http as api } from '@/lib/http';

export interface DailyTrend {
  date: string;
  sync_success: number;
  sync_conflicts: number;
  ai_requests: number;
  inventory_changes: number;
}

export interface SyncLogEntry {
  id: number;
  config_id: number | null;
  status: string;
  started_at: string | null;
  completed_at: string | null;
}

export interface InventoryItemCard {
  id: number;
  title: string;
  price: number;
  currency: string;
  status: string;
  category: string | null;
  created_at: string | null;
}

export const useDashboardStore = defineStore('dashboard', {
  state: () => ({
    dailyStats: [] as DailyTrend[],
    syncLogs: [] as SyncLogEntry[],
    latestItems: [] as InventoryItemCard[],
    loading: false,
    error: ''
  }),
  actions: {
    async refreshAll() {
      this.loading = true;
      this.error = '';
      try {
        const [stats, logs, inventory] = await Promise.all([
          api.get<DailyTrend[]>('/dashboard/daily-stats'),
          api.get<SyncLogEntry[]>('/dashboard/sync-logs'),
          api.get<InventoryItemCard[]>('/dashboard/inventory')
        ]);
        this.dailyStats = stats.data.reverse();
        this.syncLogs = logs.data;
        this.latestItems = inventory.data;
      } catch (error) {
        this.error = (error as Error).message;
      } finally {
        this.loading = false;
      }
    }
  }
});
