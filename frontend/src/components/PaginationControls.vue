<template>
  <div class="flex flex-wrap items-center justify-between gap-3 border-t pt-4">
    <div class="text-sm text-slate-500">
      第 <span class="font-semibold text-slate-900">{{ currentPage }}</span> / {{ totalPages }} 页 ·
      共 {{ total }} 条
    </div>
    <div class="flex items-center gap-2">
      <button
        class="rounded border px-3 py-1 text-sm"
        :disabled="currentPage <= 1"
        @click="$emit('previous')"
      >
        上一页
      </button>
      <div class="flex items-center gap-1">
        <button
          v-for="page in visiblePages"
          :key="page"
          class="rounded px-3 py-1 text-sm"
          :class="page === currentPage ? 'bg-indigo-600 text-white' : 'bg-slate-100 text-slate-600'"
          @click="$emit('jump', page)"
        >
          {{ page }}
        </button>
      </div>
      <button
        class="rounded border px-3 py-1 text-sm"
        :disabled="currentPage >= totalPages"
        @click="$emit('next')"
      >
        下一页
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

const props = defineProps<{
  currentPage: number;
  totalPages: number;
  total: number;
}>();

defineEmits<{
  (event: 'previous'): void;
  (event: 'next'): void;
  (event: 'jump', page: number): void;
}>();

const visiblePages = computed(() => {
  const pages: number[] = [];
  const maxButtons = 5;
  let start = Math.max(1, props.currentPage - 2);
  let end = Math.min(props.totalPages, start + maxButtons - 1);
  if (end - start < maxButtons - 1) {
    start = Math.max(1, end - maxButtons + 1);
  }
  for (let i = start; i <= end; i += 1) {
    pages.push(i);
  }
  return pages;
});
</script>
