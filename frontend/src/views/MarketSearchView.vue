<template>
  <div class="space-y-6">
    <section class="rounded-3xl bg-gradient-to-r from-indigo-600 to-purple-600 px-6 py-8 text-white shadow-xl">
      <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <p class="text-sm tracking-widest uppercase text-white/80">智能检索 · 多源联动</p>
          <h1 class="text-3xl font-semibold">跨平台市场中心</h1>
          <p class="mt-2 max-w-2xl text-white/80">
            结合 AI 推荐、库存同步与角色权限，为不同用户提供专属的二手交易体验。管理员可快速定位异常，卖家可查看曝光数据，买家可筛选最心仪的物品。
          </p>
        </div>
        <div class="rounded-2xl bg-white/10 p-4 text-sm">
          <p class="text-xs uppercase text-white/70">当前筛选结果</p>
          <p class="text-3xl font-semibold">{{ total }} 条</p>
          <p class="text-white/70">第 {{ page }} / {{ totalPages }} 页</p>
        </div>
      </div>
    </section>

    <div class="grid gap-6 lg:grid-cols-[320px,1fr]">
      <aside class="space-y-4">
        <AdvancedSearchPanel />
        <article class="rounded-2xl bg-white p-4 shadow">
          <h3 class="text-base font-semibold text-slate-800">热门主题</h3>
          <ul class="mt-3 space-y-2 text-sm text-slate-600">
            <li class="flex items-center justify-between">
              <span>高频曝光</span>
              <span class="rounded-full bg-indigo-50 px-2 py-0.5 text-indigo-600">实时</span>
            </li>
            <li class="flex items-center justify-between">
              <span>价格偏高</span>
              <span>14</span>
            </li>
            <li class="flex items-center justify-between">
              <span>待审核</span>
              <span>7</span>
            </li>
          </ul>
        </article>
      </aside>

      <section class="space-y-4">
        <header class="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p class="text-sm text-slate-500">{{ heroSubtitle }}</p>
            <h2 class="text-2xl font-semibold text-slate-900">精选结果</h2>
          </div>
          <div class="flex items-center gap-2">
            <button class="rounded border px-3 py-1 text-sm" :disabled="loading" @click="refresh">
              {{ loading ? '刷新中...' : '刷新' }}
            </button>
            <span v-if="isAdmin" class="rounded-full bg-amber-100 px-3 py-1 text-xs text-amber-700">管理员视图</span>
          </div>
        </header>

        <div v-if="results.length === 0" class="rounded-2xl border border-dashed border-slate-200 p-8 text-center text-slate-500">
          <p class="text-lg font-medium">暂无结果</p>
          <p class="mt-1 text-sm">试试调整筛选条件，或切换分类查看。</p>
        </div>

        <div v-else class="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          <article
            v-for="item in results"
            :key="item.id"
            class="group rounded-2xl border border-slate-100 bg-white p-4 shadow-sm transition hover:-translate-y-1 hover:shadow-lg"
          >
            <div class="flex items-center justify-between text-xs uppercase text-slate-400">
              <span>{{ item.category ?? '未分类' }}</span>
              <span>{{ formatDate(item.updated_at) }}</span>
            </div>
            <h3 class="mt-2 text-lg font-semibold text-slate-900">{{ item.title }}</h3>
            <p class="mt-1 text-2xl font-bold text-indigo-600">
              {{ item.price.toFixed(2) }}
              <span class="text-base font-medium text-slate-500">{{ item.currency }}</span>
            </p>
            <div class="mt-3 flex items-center gap-2 text-sm text-slate-500">
              <span class="rounded-full bg-slate-100 px-2 py-0.5 text-xs">{{ item.status }}</span>
              <span v-if="isAdmin" class="rounded-full bg-rose-50 px-2 py-0.5 text-xs text-rose-600">
                卖家 #{{ item.seller_id }}
              </span>
            </div>
            <footer class="mt-4 flex items-center justify-between text-sm text-slate-500">
              <span>同步版本 {{ item.id }}</span>
              <button class="text-indigo-600" type="button">查看详情 →</button>
            </footer>
          </article>
        </div>

        <PaginationControls
          :current-page="page"
          :total-pages="totalPages"
          :total="total"
          @next="nextPage"
          @previous="previousPage"
          @jump="handleJump"
        />

        <p v-if="error" class="text-sm text-rose-500">{{ error }}</p>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue';
import { storeToRefs } from 'pinia';

import AdvancedSearchPanel from '@/components/AdvancedSearchPanel.vue';
import PaginationControls from '@/components/PaginationControls.vue';
import { useAuthStore } from '@/stores/auth';
import { useMarketSearchStore } from '@/stores/marketSearch';

const marketStore = useMarketSearchStore();
const authStore = useAuthStore();
const { results, total, loading, error, page, totalPages } = storeToRefs(marketStore);
const isAdmin = computed(() => authStore.isAdmin);

const heroSubtitle = computed(() =>
  isAdmin.value ? '管理员可查看卖家和状态详情' : '智能推荐为你筛选更合适的物品'
);

function refresh() {
  marketStore.search();
}

function nextPage() {
  marketStore.nextPage();
}

function previousPage() {
  marketStore.previousPage();
}

function handleJump(targetPage: number) {
  marketStore.goToPage(targetPage);
}

function formatDate(input: string | null) {
  if (!input) return '—';
  return new Date(input).toLocaleDateString();
}

onMounted(() => {
  marketStore.fetchCategories();
  marketStore.search();
});
</script>
