<template>
  <div class="space-y-4 rounded-xl bg-white p-4 shadow">
    <header class="flex items-center justify-between">
      <div>
        <p class="text-sm text-slate-500">复杂筛选</p>
        <h2 class="text-lg font-semibold">跨库搜索</h2>
      </div>
      <div class="flex gap-2">
        <button class="text-sm text-slate-500" type="button" @click="handleReset">重置</button>
        <button
          class="rounded bg-indigo-600 px-4 py-1 text-sm text-white"
          type="button"
          :disabled="loading"
          @click="handleSearch"
        >
          {{ loading ? '搜索中...' : '搜索' }}
        </button>
      </div>
    </header>

    <div class="grid gap-4 lg:grid-cols-2">
      <label class="text-sm text-slate-600">
        关键词
        <input v-model="filters.keyword" class="mt-1 w-full rounded border px-3 py-2" placeholder="标题/描述" />
      </label>
      <label class="text-sm text-slate-600">
        分类
        <select v-model="filters.categoryIds" multiple class="mt-1 w-full rounded border px-3 py-2 h-24">
          <option v-for="cat in categories" :key="cat.id" :value="cat.id">{{ cat.name }}</option>
        </select>
      </label>
      <div class="text-sm text-slate-600">
        状态
        <div class="mt-1 flex flex-wrap gap-3">
          <label class="flex items-center gap-1 text-xs">
            <input v-model="filters.status" type="checkbox" value="active" />
            Active
          </label>
          <label class="flex items-center gap-1 text-xs">
            <input v-model="filters.status" type="checkbox" value="published" />
            Published
          </label>
          <label class="flex items-center gap-1 text-xs">
            <input v-model="filters.status" type="checkbox" value="draft" />
            Draft
          </label>
        </div>
      </div>
      <div class="grid grid-cols-2 gap-2 text-sm text-slate-600">
        <label>
          价格下限
          <input v-model.number="filters.priceMin" type="number" min="0" class="mt-1 w-full rounded border px-2 py-1" />
        </label>
        <label>
          价格上限
          <input v-model.number="filters.priceMax" type="number" min="0" class="mt-1 w-full rounded border px-2 py-1" />
        </label>
      </div>
      <label v-if="isAdmin" class="text-sm text-slate-600">
        指定卖家 ID
        <input v-model.number="filters.sellerId" type="number" min="1" class="mt-1 w-full rounded border px-2 py-1" />
      </label>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { storeToRefs } from 'pinia';

import { useAuthStore } from '@/stores/auth';
import { useMarketSearchStore } from '@/stores/marketSearch';

const marketStore = useMarketSearchStore();
const { filters, loading, categories } = storeToRefs(marketStore);
const authStore = useAuthStore();
const isAdmin = computed(() => authStore.isAdmin);

function handleSearch() {
  marketStore.search();
}

function handleReset() {
  marketStore.reset();
}
</script>
