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
        JOIN <span class="text-primary">PHOENIX</span>
      </h2>
      <p class="mt-2 text-center text-[10px] font-bold uppercase tracking-[0.3em] text-gray-500">
        Become a Certified Auto Parts Merchant
      </p>
    </div>

    <div class="mt-10 sm:mx-auto sm:w-full sm:max-w-md relative z-10">
      <div class="bg-white/5 backdrop-blur-xl p-10 rounded-2xl border border-white/10 shadow-2xl">
        <div class="space-y-5">
          <!-- 错误提示 -->
          <div v-if="errorMessage" class="rounded-lg bg-red-500/10 border border-red-500/20 p-4">
            <div class="text-xs font-bold uppercase tracking-widest text-red-400">{{ errorMessage }}</div>
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div>
              <label for="username" class="block text-[10px] font-black uppercase tracking-widest text-gray-400 mb-2">商户名称 Name</label>
              <input v-model="form.username" id="username" type="text" required placeholder="Merchant Name" class="block w-full rounded-xl border-0 bg-white/5 py-3 px-4 text-white shadow-sm ring-1 ring-inset ring-white/10 placeholder:text-gray-600 focus:ring-2 focus:ring-inset focus:ring-primary sm:text-sm transition-all" />
            </div>
            <div>
              <label for="licenseId" class="block text-[10px] font-black uppercase tracking-widest text-gray-400 mb-2">执照编号 License</label>
              <input v-model="form.licenseId" id="licenseId" type="text" required placeholder="8-12 digits" class="block w-full rounded-xl border-0 bg-white/5 py-3 px-4 text-white shadow-sm ring-1 ring-inset ring-white/10 placeholder:text-gray-600 focus:ring-2 focus:ring-inset focus:ring-primary sm:text-sm transition-all" />
            </div>
          </div>

          <div>
            <label for="email" class="block text-[10px] font-black uppercase tracking-widest text-gray-400 mb-2">联系邮箱 Email</label>
            <input v-model="form.email" id="email" type="email" required placeholder="your@email.com" class="block w-full rounded-xl border-0 bg-white/5 py-3 px-4 text-white shadow-sm ring-1 ring-inset ring-white/10 placeholder:text-gray-600 focus:ring-2 focus:ring-inset focus:ring-primary sm:text-sm transition-all" />
          </div>

          <div>
            <label for="password" class="block text-[10px] font-black uppercase tracking-widest text-gray-400 mb-2">设置密码 Password</label>
            <input v-model="form.password" id="password" type="password" required placeholder="Min 6 characters" class="block w-full rounded-xl border-0 bg-white/5 py-3 px-4 text-white shadow-sm ring-1 ring-inset ring-white/10 placeholder:text-gray-600 focus:ring-2 focus:ring-inset focus:ring-primary sm:text-sm transition-all" />
          </div>

          <div>
            <label for="confirmPassword" class="block text-[10px] font-black uppercase tracking-widest text-gray-400 mb-2">确认密码 Confirm</label>
            <input v-model="form.confirmPassword" id="confirmPassword" type="password" required placeholder="Repeat password" class="block w-full rounded-xl border-0 bg-white/5 py-3 px-4 text-white shadow-sm ring-1 ring-inset ring-white/10 placeholder:text-gray-600 focus:ring-2 focus:ring-inset focus:ring-primary sm:text-sm transition-all" />
          </div>

          <div class="pt-4">
            <button 
              @click="handleRegister" 
              :disabled="isLoading"
              type="button" 
              class="flex w-full justify-center rounded-xl bg-primary px-4 py-4 text-xs font-black uppercase tracking-[0.2em] text-white shadow-lg shadow-primary/20 hover:bg-primary/90 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary disabled:opacity-50 transition-all active:scale-[0.98]"
            >
              {{ isLoading ? 'Processing...' : '提交入驻申请 Join Now' }}
            </button>
          </div>
        </div>

        <div class="mt-10 pt-8 border-t border-white/5 text-center">
          <p class="text-[10px] font-bold uppercase tracking-widest text-gray-500">
            已有商户账号？
            <RouterLink to="/login" class="text-primary hover:text-white transition-colors ml-2">
              立即登录 Login
            </RouterLink>
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { http as api } from '@/lib/http'

const router = useRouter()
const isLoading = ref(false)
const errorMessage = ref('')

const form = ref({
  username: '',
  email: '',
  licenseId: '',
  password: '',
  confirmPassword: ''
})

const handleRegister = async () => {
  errorMessage.value = ''
  
  // 前端验证
  if (form.value.username.length < 3 || form.value.username.length > 20) {
    errorMessage.value = '商户名称需要3-20个字符'
    return
  }
  
  if (!/^[0-9]{8,12}$/.test(form.value.licenseId)) {
    errorMessage.value = '执照编号需要8-12位数字'
    return
  }
  
  if (form.value.password.length < 6) {
    errorMessage.value = '密码至少需要6个字符'
    return
  }
  
  if (form.value.password !== form.value.confirmPassword) {
    errorMessage.value = '两次输入的密码不一致'
    return
  }

  isLoading.value = true
  
  try {
    await api.post('/auth/register', {
      username: form.value.username,
      email: form.value.email,
      license_id: form.value.licenseId,
      password: form.value.password,
      confirm_password: form.value.confirmPassword
    })
    
    alert('注册成功，请登录')
    router.push('/login')
    
  } catch (error: any) {
    console.error(error)
    const detail = error.response?.data?.detail
    if (Array.isArray(detail)) {
      errorMessage.value = detail.map((d: any) => d.msg).join(', ')
    } else if (typeof detail === 'string') {
      errorMessage.value = detail
    } else {
      errorMessage.value = '注册失败，请稍后重试'
    }
  } finally {
    isLoading.value = false
  }
}
</script>