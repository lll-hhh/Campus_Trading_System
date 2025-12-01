<template>
  <div class="flex min-h-full flex-1 flex-col justify-center px-6 py-12 lg:px-8">
    <div class="sm:mx-auto sm:w-full sm:max-w-sm">
      <h2 class="mt-10 text-center text-2xl font-bold leading-9 tracking-tight text-gray-900">
        注册新账户
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
            <input v-model="form.username" id="username" type="text" required placeholder="3-20个字符" class="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6" />
          </div>
        </div>

        <div>
          <label for="email" class="block text-sm font-medium leading-6 text-gray-900">邮箱</label>
          <div class="mt-2">
            <input v-model="form.email" id="email" type="email" required placeholder="your@email.com" class="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6" />
          </div>
        </div>

        <!-- 新增：学号字段 -->
        <div>
          <label for="studentId" class="block text-sm font-medium leading-6 text-gray-900">学号</label>
          <div class="mt-2">
            <input v-model="form.studentId" id="studentId" type="text" required placeholder="8-12位数字" class="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6" />
          </div>
        </div>

        <div>
          <label for="password" class="block text-sm font-medium leading-6 text-gray-900">密码</label>
          <div class="mt-2">
            <input v-model="form.password" id="password" type="password" required placeholder="至少6个字符" class="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6" />
          </div>
        </div>

        <div>
          <label for="confirmPassword" class="block text-sm font-medium leading-6 text-gray-900">确认密码</label>
          <div class="mt-2">
            <input v-model="form.confirmPassword" id="confirmPassword" type="password" required placeholder="再次输入密码" class="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6" />
          </div>
        </div>

        <div>
          <button 
            @click="handleRegister" 
            :disabled="isLoading"
            type="button" 
            class="flex w-full justify-center rounded-md bg-indigo-600 px-3 py-1.5 text-sm font-semibold leading-6 text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 disabled:opacity-50"
          >
            {{ isLoading ? '注册中...' : '注册' }}
          </button>
        </div>
      </div>

      <p class="mt-10 text-center text-sm text-gray-500">
        已有账号？
        <RouterLink to="/login" class="font-semibold leading-6 text-indigo-600 hover:text-indigo-500">
          去登录
        </RouterLink>
      </p>
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
  studentId: '',
  password: '',
  confirmPassword: ''
})

const handleRegister = async () => {
  errorMessage.value = ''
  
  // 前端验证
  if (form.value.username.length < 3 || form.value.username.length > 20) {
    errorMessage.value = '用户名需要3-20个字符'
    return
  }
  
  if (!/^[0-9]{8,12}$/.test(form.value.studentId)) {
    errorMessage.value = '学号需要8-12位数字'
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
      student_id: form.value.studentId,
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