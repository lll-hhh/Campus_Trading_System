<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { 
  NCard, 
  NForm, 
  NFormItem, 
  NInput, 
  NButton, 
  NCheckbox, 
  NSpace,
  NTabs,
  NTabPane,
  useMessage 
} from 'naive-ui'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const message = useMessage()
const authStore = useAuthStore()

const loading = ref(false)

// 登录表单
const loginForm = reactive({
  username: '',
  password: '',
  remember: false
})

// 注册表单
const registerForm = reactive({
  username: '',
  email: '',
  studentId: '',
  password: '',
  confirmPassword: '',
  agreeTerms: false
})

// 表单校验规则
const loginRules = {
  username: [
    { required: true, message: '请输入用户名或学号', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位', trigger: 'blur' }
  ]
}

const registerRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度为3-20个字符', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' }
  ],
  studentId: [
    { required: true, message: '请输入学号', trigger: 'blur' },
    { 
      pattern: /^[0-9]{8,12}$/, 
      message: '学号应为8-12位数字', 
      trigger: 'blur' 
    }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    {
      validator: (rule: any, value: string) => {
        return value === registerForm.password
      },
      message: '两次输入的密码不一致',
      trigger: 'blur'
    }
  ],
  agreeTerms: [
    {
      validator: (rule: any, value: boolean) => {
        return value === true
      },
      message: '请阅读并同意服务协议',
      trigger: 'change'
    }
  ]
}

// 登录处理
const handleLogin = async () => {
  loading.value = true
  try {
    // TODO: 调用后端登录API
    await new Promise(resolve => setTimeout(resolve, 1000)) // 模拟API调用
    
    authStore.login({
      username: loginForm.username,
      token: 'mock-token-' + Date.now()
    })
    
    message.success('登录成功！')
    router.push('/marketplace')
  } catch (error: any) {
    message.error(error.message || '登录失败，请重试')
  } finally {
    loading.value = false
  }
}

// 注册处理
const handleRegister = async () => {
  loading.value = true
  try {
    // TODO: 调用后端注册API
    await new Promise(resolve => setTimeout(resolve, 1000)) // 模拟API调用
    
    message.success('注册成功！请登录')
    // 切换到登录标签
  } catch (error: any) {
    message.error(error.message || '注册失败，请重试')
  } finally {
    loading.value = false
  }
}

// 忘记密码
const handleForgotPassword = () => {
  router.push('/forgot-password')
}
</script>

<template>
  <div class="login-view">
    <div class="login-container">
      <!-- 左侧装饰 -->
      <div class="login-decoration">
        <div class="decoration-content">
          <h1>🎓 校园交易平台</h1>
          <p>安全、便捷、高效的校园二手交易平台</p>
          <div class="features">
            <div class="feature-item">
              <span class="icon">✅</span>
              <span>实名认证 安全可靠</span>
            </div>
            <div class="feature-item">
              <span class="icon">💬</span>
              <span>即时聊天 高效沟通</span>
            </div>
            <div class="feature-item">
              <span class="icon">📦</span>
              <span>丰富商品 应有尽有</span>
            </div>
            <div class="feature-item">
              <span class="icon">⚡</span>
              <span>快速交易 便捷支付</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧表单 -->
      <div class="login-form-wrapper">
        <n-card class="login-card" :bordered="false">
          <n-tabs type="line" animated size="large">
            <!-- 登录 -->
            <n-tab-pane name="login" tab="登录">
              <n-form
                :model="loginForm"
                :rules="loginRules"
                size="large"
                label-placement="left"
              >
                <n-form-item path="username">
                  <n-input
                    v-model:value="loginForm.username"
                    placeholder="用户名/学号"
                    clearable
                  >
                    <template #prefix>
                      <span>👤</span>
                    </template>
                  </n-input>
                </n-form-item>

                <n-form-item path="password">
                  <n-input
                    v-model:value="loginForm.password"
                    type="password"
                    show-password-on="click"
                    placeholder="密码"
                  >
                    <template #prefix>
                      <span>🔒</span>
                    </template>
                  </n-input>
                </n-form-item>

                <n-space justify="space-between" style="width: 100%">
                  <n-checkbox v-model:checked="loginForm.remember">
                    记住我
                  </n-checkbox>
                  <n-button text type="primary" @click="handleForgotPassword">
                    忘记密码？
                  </n-button>
                </n-space>

                <n-button
                  type="primary"
                  block
                  size="large"
                  :loading="loading"
                  @click="handleLogin"
                  style="margin-top: 24px"
                >
                  登录
                </n-button>
              </n-form>
            </n-tab-pane>

            <!-- 注册 -->
            <n-tab-pane name="register" tab="注册">
              <n-form
                :model="registerForm"
                :rules="registerRules"
                size="large"
                label-placement="left"
              >
                <n-form-item path="username">
                  <n-input
                    v-model:value="registerForm.username"
                    placeholder="用户名"
                    clearable
                  >
                    <template #prefix>
                      <span>👤</span>
                    </template>
                  </n-input>
                </n-form-item>

                <n-form-item path="email">
                  <n-input
                    v-model:value="registerForm.email"
                    placeholder="邮箱"
                    clearable
                  >
                    <template #prefix>
                      <span>📧</span>
                    </template>
                  </n-input>
                </n-form-item>

                <n-form-item path="studentId">
                  <n-input
                    v-model:value="registerForm.studentId"
                    placeholder="学号"
                    clearable
                  >
                    <template #prefix>
                      <span>🎓</span>
                    </template>
                  </n-input>
                </n-form-item>

                <n-form-item path="password">
                  <n-input
                    v-model:value="registerForm.password"
                    type="password"
                    show-password-on="click"
                    placeholder="密码"
                  >
                    <template #prefix>
                      <span>🔒</span>
                    </template>
                  </n-input>
                </n-form-item>

                <n-form-item path="confirmPassword">
                  <n-input
                    v-model:value="registerForm.confirmPassword"
                    type="password"
                    show-password-on="click"
                    placeholder="确认密码"
                  >
                    <template #prefix>
                      <span>🔒</span>
                    </template>
                  </n-input>
                </n-form-item>

                <n-form-item path="agreeTerms">
                  <n-checkbox v-model:checked="registerForm.agreeTerms">
                    我已阅读并同意
                    <n-button text type="primary">《服务协议》</n-button>
                    和
                    <n-button text type="primary">《隐私政策》</n-button>
                  </n-checkbox>
                </n-form-item>

                <n-button
                  type="primary"
                  block
                  size="large"
                  :loading="loading"
                  @click="handleRegister"
                  style="margin-top: 16px"
                >
                  注册
                </n-button>
              </n-form>
            </n-tab-pane>
          </n-tabs>
        </n-card>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-view {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.login-container {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 40px;
  max-width: 1200px;
  width: 100%;
}

.login-decoration {
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.decoration-content h1 {
  font-size: 48px;
  margin-bottom: 16px;
  font-weight: bold;
}

.decoration-content > p {
  font-size: 20px;
  margin-bottom: 48px;
  opacity: 0.9;
}

.features {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 16px;
  font-size: 18px;
}

.feature-item .icon {
  font-size: 32px;
  width: 50px;
  height: 50px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 12px;
}

.login-form-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
}

.login-card {
  width: 100%;
  max-width: 480px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  border-radius: 16px;
}

/* 响应式设计 */
@media (max-width: 968px) {
  .login-container {
    grid-template-columns: 1fr;
  }
  
  .login-decoration {
    display: none;
  }
}
</style>
