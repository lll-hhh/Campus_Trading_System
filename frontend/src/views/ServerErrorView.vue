<template>
  <div class="error-page server-error">
    <div class="error-container">
      <div class="error-code">500</div>
      <div class="error-title">服务器错误</div>
      <div class="error-message">
        抱歉，服务器遇到了一些问题，请稍后再试
      </div>
      <div class="error-illustration">
        <div class="illustration-placeholder">⚠️</div>
      </div>
      <n-space class="error-actions">
        <n-button type="primary" @click="reload">
          刷新页面
        </n-button>
        <n-button @click="goHome">
          返回首页
        </n-button>
      </n-space>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { NSpace, NButton } from 'naive-ui'

const router = useRouter()

const reload = () => {
  window.location.reload()
}

const goHome = () => {
  router.push('/marketplace')
}
</script>

<style scoped>
.error-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
}

.error-container {
  text-align: center;
  padding: 48px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  max-width: 500px;
}

.error-code {
  font-size: 120px;
  font-weight: bold;
  background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  line-height: 1;
  margin-bottom: 24px;
}

.error-title {
  font-size: 32px;
  font-weight: 600;
  color: #333;
  margin-bottom: 16px;
}

.error-message {
  font-size: 16px;
  color: #666;
  margin-bottom: 32px;
  line-height: 1.6;
}

.error-illustration {
  margin-bottom: 32px;
}

.illustration-placeholder {
  font-size: 80px;
  opacity: 0.5;
}

.error-actions {
  justify-content: center;
}
</style>
