<template>
  <transition
    :name="transitionName"
    mode="out-in"
    @before-enter="beforeEnter"
    @enter="enter"
    @after-enter="afterEnter"
  >
    <slot />
  </transition>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const transitionName = ref('fade')

// 监听路由变化，决定过渡效果
watch(
  () => route.path,
  (to, from) => {
    if (!from) {
      transitionName.value = 'fade'
      return
    }

    // 根据路由层级决定动画方向
    const toDepth = to.split('/').length
    const fromDepth = from.split('/').length

    if (toDepth > fromDepth) {
      transitionName.value = 'slide-left'
    } else if (toDepth < fromDepth) {
      transitionName.value = 'slide-right'
    } else {
      transitionName.value = 'fade'
    }
  }
)

const beforeEnter = () => {
  // 滚动到顶部
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

const enter = () => {
  // 可以添加进入动画的逻辑
}

const afterEnter = () => {
  // 动画完成后的回调
}
</script>

<style scoped>
/* 淡入淡出 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* 左滑（前进） */
.slide-left-enter-active,
.slide-left-leave-active {
  transition: all 0.3s ease;
}

.slide-left-enter-from {
  opacity: 0;
  transform: translateX(30px);
}

.slide-left-leave-to {
  opacity: 0;
  transform: translateX(-30px);
}

/* 右滑（后退） */
.slide-right-enter-active,
.slide-right-leave-active {
  transition: all 0.3s ease;
}

.slide-right-enter-from {
  opacity: 0;
  transform: translateX(-30px);
}

.slide-right-leave-to {
  opacity: 0;
  transform: translateX(30px);
}
</style>
