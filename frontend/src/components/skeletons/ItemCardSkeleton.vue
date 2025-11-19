<template>
  <div class="item-card-skeleton">
    <n-skeleton height="200px" :sharp="false" />
    <div class="skeleton-content">
      <n-skeleton text :repeat="2" />
      <n-skeleton text width="60%" />
      <n-space style="margin-top: 12px">
        <n-skeleton circle size="small" />
        <n-skeleton text width="80px" style="height: 20px" />
      </n-space>
    </div>
  </div>
</template>

<script setup lang="ts">
import { NSkeleton, NSpace } from 'naive-ui'
</script>

<style scoped>
.item-card-skeleton {
  border: 1px solid #f0f0f0;
  border-radius: 8px;
  overflow: hidden;
  background: white;
}

.skeleton-content {
  padding: 16px;
}
</style>
