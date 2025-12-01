<template>
  <div class="flex min-h-full flex-1 flex-col justify-center px-6 py-12 lg:px-8">
    <div class="sm:mx-auto sm:w-full sm:max-w-sm">
      <h2 class="mt-10 text-center text-2xl font-bold leading-9 tracking-tight text-gray-900">
        登录您的账户
      </h2>
    </div>

    <div class="mt-10 sm:mx-auto sm:w-full sm:max-w-sm">
      <div class="space-y-6">
        <!-- 错误提示 -->
        <div v-if="errorMessage" class="rounded-md bg-red-50 p-4">
          <div class="text-sm text-red-700">{{ errorMessage }}</div>
        </div>

        <div>
          <label for="username" class="block text-sm font-medium leading-6 text-gray-900">用户名</label>
          <div class="mt-2">
            <input 
              v-model="form.username" 
              id="username" 
              type="text" 
              required 
              placeholder="请输入用户名"
              class="block w-full rounded-md border-0 py-1.5 px-3 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6" 
            />
          </div>
        </div>

        <div>
          <label for="password" class="block text-sm font-medium leading-6 text-gray-900">密码</label>
          <div class="mt-2">
            <input 
              v-model="form.password" 
              id="password" 
              type="password" 
              required 
              placeholder="请输入密码"
              class="block w-full rounded-md border-0 py-1.5 px-3 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6" 
            />
          </div>
        </div>

        <div>
          <button 
            @click="handleLogin" 
            :disabled="isLoading"
            type="button" 
            class="flex w-full justify-center rounded-md bg-indigo-600 px-3 py-1.5 text-sm font-semibold leading-6 text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 disabled:opacity-50"
          >
            {{ isLoading ? '登录中...' : '登录' }}
          </button>
        </div>
      </div>

      <p class="mt-10 text-center text-sm text-gray-500">
        还没有账号？
        <RouterLink to="/register" class="font-semibold leading-6 text-indigo-600 hover:text-indigo-500">
          立即注册
        </RouterLink>
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const form = ref({
  username: '',
  password: ''
})

const errorMessage = ref('')
const isLoading = computed(() => authStore.loading)

const handleLogin = async () => {
  errorMessage.value = ''
  
  if (!form.value.username || !form.value.password) {
    errorMessage.value = '请输入用户名和密码'
    return
  }

  try {
    const result = await authStore.login({
      username: form.value.username,
      password: form.value.password
    })
    
    console.log('登录成功，用户角色:', result.user.roles)
    
    // ✅ 根据角色重定向到不同首页
    if (result.isAdmin) {
      console.log('管理员用户，跳转到管理后台')
      router.push('/admin/dashboard')
    } else {
      console.log('普通用户，跳转到商品市场')
      router.push('/marketplace')
    }

  } catch (error: any) {
    console.error('登录失败:', error)
    errorMessage.value = error.message || '登录失败'
  }
}
</script>