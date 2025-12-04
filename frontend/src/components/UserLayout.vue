<script setup lang="ts">
import { NLayout, NLayoutContent, NLayoutFooter, NSpace, NButton } from 'naive-ui'
import { useRouter } from 'vue-router'

const router = useRouter()

const quickLinks = [
  { label: '关于我们', path: '/about' },
  { label: '服务协议', path: '/terms' },
  { label: '隐私政策', path: '/privacy' },
  { label: '帮助中心', path: '/help' }
]

const navigateToLink = (path: string) => {
  router.push(path)
}
</script>

<template>
  <n-layout class="user-layout">
    <!-- 移除顶部导航栏，使用App.vue的全局导航 -->

    <!-- 主要内容区域 -->
    <n-layout-content class="main-content">
      <div class="content-container">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </div>
    </n-layout-content>

    <!-- 页脚 -->
    <n-layout-footer bordered class="footer">
      <div class="footer-content">
        <div class="footer-section">
          <h4>🎓 CampuSwap</h4>
          <p>安全、便捷、高效的校园二手交易平台</p>
          <p style="color: #999; font-size: 12px">让校园资源流动起来</p>
        </div>

        <div class="footer-section">
          <h4>快速链接</h4>
          <n-space vertical :size="8">
            <a 
              v-for="link in quickLinks" 
              :key="link.path"
              @click="navigateToLink(link.path)"
              class="footer-link"
            >
              {{ link.label }}
            </a>
          </n-space>
        </div>

        <div class="footer-section">
          <h4>联系我们</h4>
          <n-space vertical :size="8">
            <span>📧 support@campus-trade.com</span>
            <span>📱 400-123-4567</span>
            <span>🕒 工作时间: 9:00-18:00</span>
          </n-space>
        </div>

        <div class="footer-section">
          <h4>关注我们</h4>
          <n-space :size="12">
            <n-button circle secondary>微</n-button>
            <n-button circle secondary>博</n-button>
            <n-button circle secondary>Q</n-button>
            <n-button circle secondary>抖</n-button>
          </n-space>
        </div>
      </div>

      <div class="footer-bottom">
        <p>© 2024 CampuSwap All Rights Reserved</p>
        <p>备案号: 京ICP备12345678号</p>
      </div>
    </n-layout-footer>
  </n-layout>
</template>

<style scoped>
.user-layout {
  min-height: 100vh;
  background-color: #f5f7fa;
}

.main-content {
  min-height: calc(100vh - 250px); /* 只减去页脚高度 */
  padding: 24px 0;
}

.content-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 24px;
}

/* 页面切换动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* 页脚样式 */
.footer {
  background-color: #fff;
  border-top: 1px solid #e0e0e0;
}

.footer-content {
  max-width: 1400px;
  margin: 0 auto;
  padding: 40px 24px;
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1fr;
  gap: 40px;
}

.footer-section h4 {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
}

.footer-section p {
  margin: 4px 0;
  font-size: 14px;
  color: #666;
}

.footer-section span {
  display: block;
  font-size: 14px;
  color: #666;
}

.footer-link {
  display: block;
  font-size: 14px;
  color: #666;
  cursor: pointer;
  transition: color 0.2s;
}

.footer-link:hover {
  color: #18a058;
}

.footer-bottom {
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px 24px;
  border-top: 1px solid #f0f0f0;
  text-align: center;
  color: #999;
  font-size: 12px;
}

.footer-bottom p {
  margin: 4px 0;
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .footer-content {
    grid-template-columns: 1fr 1fr;
    gap: 24px;
  }
}

@media (max-width: 768px) {
  .footer-content {
    grid-template-columns: 1fr;
    gap: 20px;
  }
  
  .main-content {
    padding: 16px 0;
  }
  
  .content-container {
    padding: 0 16px;
  }
}
</style>
