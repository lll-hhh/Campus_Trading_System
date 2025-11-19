<template>
  <div class="error-page">
    <div class="error-container">
      <div class="error-code">404</div>
      <div class="error-title">页面不存在</div>
      <div class="error-message">
        抱歉，您访问的页面不存在或已被删除
      </div>
      <div class="error-illustration">
        <div class="illustration-placeholder">🔍</div>
      </div>
      <n-space class="error-actions">
        <n-button type="primary" @click="goHome">
          返回首页
        </n-button>
        <n-button @click="goBack">
          返回上一页
        </n-button>
      </n-space>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { NSpace, NButton } from 'naive-ui'

const router = useRouter()

const goHome = () => {
  router.push('/marketplace')
}

const goBack = () => {
  router.back()
}
</script>

<style scoped>
.error-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
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
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
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
