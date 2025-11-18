import type { AxiosError } from 'axios';
import { defineStore } from 'pinia';

import api from '@/lib/http';

interface DailyStat {
  date: string | null;
  sync_success: number;
  sync_conflicts: number;
}

export interface SyncStatus {
  targets: string[];
  mode: string;
  environment: string;
  conflicts: number;
  last_run: string | null;
  daily_stat: DailyStat;
}

export interface ConflictRecord {
  id: number;
  table: string;
  record_id: string;
  source: string;
  target: string;
  created_at: string;
}

type ConflictStrategy = 'source' | 'target' | 'manual';

export const useSyncStore = defineStore('sync', {
  state: () => ({
    status: null as SyncStatus | null,
    conflicts: [] as ConflictRecord[],
    loadingStatus: false,
    loadingConflicts: false,
    runningManual: false,
    lastUpdated: null as string | null,
    error: null as string | null
  }),
  getters: {
    successRate(state) {
      const success = state.status?.daily_stat.sync_success ?? 0;
      const conflicts = state.status?.daily_stat.sync_conflicts ?? 0;
      const total = success + conflicts;
      if (total === 0) {
        return 100;
      }
      return Number(((success / total) * 100).toFixed(1));
    }
  },
  actions: {
    handleError(error: unknown) {
      if ((error as AxiosError)?.response?.status === 403) {
        this.error = '需要管理员权限查看该数据';
        return;
      }
      this.error = (error as Error).message;
    },
    async fetchStatus() {
      this.loadingStatus = true;
      this.error = null;
      try {
        const { data } = await api.get<SyncStatus>('/sync/status');
        this.status = data;
        this.lastUpdated = new Date().toISOString();
      } catch (error) {
        this.handleError(error);
      } finally {
        this.loadingStatus = false;
      }
    },
    async fetchConflicts() {
      this.loadingConflicts = true;
      this.error = null;
      try {
        const { data } = await api.get<ConflictRecord[]>('/sync/conflicts');
        this.conflicts = data;
      } catch (error) {
        this.handleError(error);
      } finally {
        this.loadingConflicts = false;
      }
    },
    async triggerManualRun() {
      this.runningManual = true;
      this.error = null;
      try {
        await api.post('/sync/run');
        await Promise.all([this.fetchStatus(), this.fetchConflicts()]);
      } catch (error) {
        this.handleError(error);
      } finally {
        this.runningManual = false;
      }
    },
    async resolveConflict(id: number, strategy: ConflictStrategy) {
      try {
        await api.post(`/sync/conflicts/${id}/resolve`, { strategy });
        await this.fetchConflicts();
      } catch (error) {
        this.handleError(error);
        throw error;
      }
    }
  }
});
