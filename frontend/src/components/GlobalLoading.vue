<template>
  <transition name="fade">
    <div v-if="loading" class="global-loading">
      <div class="loading-content">
        <n-spin size="large" />
        <div class="loading-text" v-if="text">{{ text }}</div>
      </div>
    </div>
  </transition>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { NSpin } from 'naive-ui'

const loading = ref(false)
const text = ref('')

const show = (loadingText: string = '') => {
  text.value = loadingText
  loading.value = true
}

const hide = () => {
  loading.value = false
  text.value = ''
}

// 暴露方法给父组件
defineExpose({
  show,
  hide
})
</script>

<style scoped>
.global-loading {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.loading-content {
  text-align: center;
}

.loading-text {
  margin-top: 16px;
  font-size: 14px;
  color: #666;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
