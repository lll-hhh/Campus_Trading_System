<template>
  <div class="flex min-h-screen flex-1 flex-col justify-center px-6 py-12 lg:px-8 bg-dark relative overflow-hidden">
    <!-- Background Decoration -->
    <div class="absolute top-0 left-0 w-full h-full opacity-10 pointer-events-none">
      <div class="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-primary blur-[120px] rounded-full"></div>
      <div class="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-primary blur-[120px] rounded-full"></div>
    </div>

    <div class="sm:mx-auto sm:w-full sm:max-w-sm relative z-10">
      <div class="flex justify-center mb-8">
        <div class="w-16 h-16 bg-primary rounded-full flex items-center justify-center text-white text-3xl font-bold shadow-lg shadow-primary/20">
          P
        </div>
      </div>
      <h2 class="text-center text-4xl font-black tracking-tighter text-white uppercase">
        PHOENIX <span class="text-primary">MALL</span>
      </h2>
      <p class="mt-2 text-center text-[10px] font-bold uppercase tracking-[0.3em] text-gray-500">
        Professional Auto Parts Trading Platform
      </p>
    </div>

    <div class="mt-10 sm:mx-auto sm:w-full sm:max-w-md relative z-10">
      <div class="bg-white/5 backdrop-blur-xl p-10 rounded-2xl border border-white/10 shadow-2xl">
        <div class="space-y-6">
          <!-- 错误提示 -->
          <div v-if="errorMessage" class="rounded-lg bg-red-500/10 border border-red-500/20 p-4">
            <div class="text-xs font-bold uppercase tracking-widest text-red-400">{{ errorMessage }}</div>
          </div>

          <div>
            <label for="username" class="block text-[10px] font-black uppercase tracking-widest text-gray-400 mb-2">商户账号 / 邮箱 Account</label>
            <div class="mt-2">
              <input 
                v-model="form.username" 
                id="username" 
                type="text" 
                required 
                placeholder="Enter your account"
                class="block w-full rounded-xl border-0 bg-white/5 py-3 px-4 text-white shadow-sm ring-1 ring-inset ring-white/10 placeholder:text-gray-600 focus:ring-2 focus:ring-inset focus:ring-primary sm:text-sm transition-all" 
              />
            </div>
          </div>

          <div>
            <div class="flex items-center justify-between">
              <label for="password" class="block text-[10px] font-black uppercase tracking-widest text-gray-400 mb-2">登录密码 Password</label>
              <div class="text-[10px] font-bold uppercase tracking-widest text-primary hover:text-white cursor-pointer transition-colors">
                忘记密码?
              </div>
            </div>
            <div class="mt-2">
              <input 
                v-model="form.password" 
                id="password" 
                type="password" 
                required 
                placeholder="Enter your password"
                class="block w-full rounded-xl border-0 bg-white/5 py-3 px-4 text-white shadow-sm ring-1 ring-inset ring-white/10 placeholder:text-gray-600 focus:ring-2 focus:ring-inset focus:ring-primary sm:text-sm transition-all" 
              />
            </div>
          </div>

          <div class="pt-4">
            <button 
              @click="handleLogin" 
              :disabled="isLoading"
              type="button" 
              class="flex w-full justify-center rounded-xl bg-primary px-4 py-4 text-xs font-black uppercase tracking-[0.2em] text-white shadow-lg shadow-primary/20 hover:bg-primary/90 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary disabled:opacity-50 transition-all active:scale-[0.98]"
            >
              {{ isLoading ? 'Verifying...' : '立即登录 Login' }}
            </button>
          </div>

          <!-- 快速登录选项 -->
          <div class="grid grid-cols-2 gap-4 mt-4">
            <button 
              @click="quickLogin('admin_test', 'password123')"
              class="flex flex-col items-center justify-center p-3 rounded-xl bg-white/5 border border-white/10 hover:bg-primary/10 hover:border-primary/30 transition-all group"
            >
              <span class="text-[10px] font-black uppercase tracking-widest text-gray-400 group-hover:text-primary">管理员</span>
              <span class="text-[8px] text-gray-600 mt-1">Admin Access</span>
            </button>
            <button 
              @click="quickLogin('user_test', 'password123')"
              class="flex flex-col items-center justify-center p-3 rounded-xl bg-white/5 border border-white/10 hover:bg-primary/10 hover:border-primary/30 transition-all group"
            >
              <span class="text-[10px] font-black uppercase tracking-widest text-gray-400 group-hover:text-primary">普通用户</span>
              <span class="text-[8px] text-gray-600 mt-1">User Access</span>
            </button>
          </div>
        </div>

        <div class="mt-10 pt-8 border-t border-white/5 text-center">
          <p class="text-[10px] font-bold uppercase tracking-widest text-gray-500">
            还没有商户账号？
            <RouterLink to="/register" class="text-primary hover:text-white transition-colors ml-2">
              申请入驻 Join Us
            </RouterLink>
          </p>
        </div>
      </div>
      
      <!-- Footer Info -->
      <div class="mt-8 flex justify-center gap-6 text-[10px] font-bold uppercase tracking-widest text-gray-600">
        <span class="hover:text-gray-400 cursor-pointer">Privacy</span>
        <span class="hover:text-gray-400 cursor-pointer">Terms</span>
        <span class="hover:text-gray-400 cursor-pointer">Support</span>
      </div>
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

const quickLogin = async (username: string, password: string) => {
  form.value.username = username
  form.value.password = password
  await handleLogin()
}

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
      console.log('普通用户，跳转到零件市场')
      router.push('/marketplace')
    }

  } catch (error: any) {
    console.error('登录失败:', error)
    errorMessage.value = error.message || '登录失败'
  }
}
</script>