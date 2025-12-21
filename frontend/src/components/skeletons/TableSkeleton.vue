<template>
  <div class="table-skeleton">
    <n-skeleton height="40px" width="100%" style="margin-bottom: 16px" />
    <div v-for="i in rows" :key="i" class="row-skeleton">
      <n-skeleton text :repeat="1" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { NSkeleton } from 'naive-ui'

defineProps<{
  rows?: number
}>()
</script>

<script lang="ts">
export default {
  name: 'TableSkeleton',
  props: {
    rows: {
      type: Number,
      default: 5
    }
  }
}
</script>

<style scoped>
.table-skeleton {
  width: 100%;
}

.row-skeleton {
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
}
</style>
