import type { AxiosError } from 'axios';
import { defineStore } from 'pinia';

import { http as api } from '@/lib/http';

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
  table_name: string;
  record_id: string;
  source: string;
  target: string;
  resolved: boolean;
  created_at: string;
  payload: Record<string, unknown>;
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
    error: null as string | null,
    resolvingConflictId: null as number | null,
    conflictMeta: {
      filter: 'unresolved' as 'all' | 'resolved' | 'unresolved',
      page: 1,
      pageSize: 10,
      total: 0,
    },
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
    async fetchConflicts(options?: { page?: number; pageSize?: number; filter?: 'all' | 'resolved' | 'unresolved' }) {
      this.loadingConflicts = true;
      this.error = null;
      if (options) {
        if (options.page) this.conflictMeta.page = options.page;
        if (options.pageSize) this.conflictMeta.pageSize = options.pageSize;
        if (options.filter) this.conflictMeta.filter = options.filter;
      }
      try {
        const params: Record<string, unknown> = {
          page: this.conflictMeta.page,
          page_size: this.conflictMeta.pageSize,
        };
        if (this.conflictMeta.filter === 'resolved') {
          params.resolved = true;
        } else if (this.conflictMeta.filter === 'unresolved') {
          params.resolved = false;
        }

        const { data } = await api.get<{ conflicts: ConflictRecord[]; total: number; page: number; page_size: number }>('/sync/conflicts', {
          params,
        });
        this.conflicts = data.conflicts;
        this.conflictMeta.total = data.total;
        this.conflictMeta.page = data.page;
        this.conflictMeta.pageSize = data.page_size;
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
      this.resolvingConflictId = id;
      try {
        await api.put(`/sync/conflicts/${id}/resolve`, { strategy });
        await this.fetchConflicts();
      } catch (error) {
        this.handleError(error);
        throw error;
      } finally {
        this.resolvingConflictId = null;
      }
    }
  }
});
