import { defineStore } from 'pinia';

import { http as api } from '@/lib/http';

export interface SearchFilters {
  keyword: string;
  categoryIds: number[];
  status: string[];
  priceMin: number | null;
  priceMax: number | null;
  sellerId: number | null;
}

export interface MarketItem {
  id: number;
  title: string;
  price: number;
  currency: string;
  status: string;
  category: string | null;
  seller_id: number;
  updated_at: string | null;
}

interface CategoryOption {
  id: number;
  name: string;
}

interface SearchResponse {
  total: number;
  items: MarketItem[];
}

export const useMarketSearchStore = defineStore('market-search', {
  state: () => ({
    filters: {
      keyword: '',
      categoryIds: [] as number[],
      status: ['active'],
      priceMin: null as number | null,
      priceMax: null as number | null,
      sellerId: null as number | null
    },
    categories: [] as CategoryOption[],
    results: [] as MarketItem[],
    total: 0,
    page: 1,
    pageSize: 12,
    totalPages: 1,
    loading: false,
    error: ''
  }),
  actions: {
    async fetchCategories() {
      try {
        const { data } = await api.get<CategoryOption[]>('/market/categories');
        this.categories = data;
      } catch (error) {
        console.warn('[market] failed to load categories', error);
      }
    },
    async search(page?: number) {
      if (page !== undefined) {
        this.page = page;
      }
      this.loading = true;
      this.error = '';
      try {
        const payload = {
          keyword: this.filters.keyword || null,
          category_ids: this.filters.categoryIds.map((id) => Number(id)),
          status: this.filters.status,
          price_min: this.filters.priceMin,
          price_max: this.filters.priceMax,
          seller_id: this.filters.sellerId,
          page: this.page,
          page_size: this.pageSize
        };
        const { data } = await api.post<SearchResponse>('/market/search', payload);
        this.results = data.items;
        this.total = data.total;
        this.totalPages = Math.max(1, Math.ceil(data.total / this.pageSize));
      } catch (error) {
        this.error = (error as Error).message;
      } finally {
        this.loading = false;
      }
    },
    reset() {
      this.filters = {
        keyword: '',
        categoryIds: [],
        status: ['active'],
        priceMin: null,
        priceMax: null,
        sellerId: null
      };
      this.page = 1;
      this.totalPages = 1;
    },
    goToPage(page: number) {
      if (page < 1 || page > this.totalPages) return;
      this.search(page);
    },
    nextPage() {
      if (this.page >= this.totalPages) return;
      this.search(this.page + 1);
    },
    previousPage() {
      if (this.page <= 1) return;
      this.search(this.page - 1);
    }
  }
});
