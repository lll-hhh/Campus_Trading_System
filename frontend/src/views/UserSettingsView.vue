<script setup lang="ts">
import { ref, onMounted } from 'vue'
import {
  NCard,
  NForm,
  NFormItem,
  NInput,
  NButton,
  NSpace,
  NSwitch,
  NSelect,
  NTabs,
  NTabPane,
  NUpload,
  NAvatar,
  NDivider,
  useMessage,
} from 'naive-ui'
import type { UploadFileInfo } from 'naive-ui'
import { http as api } from '@/lib/http'

const message = useMessage()

// 个人信息
const profileForm = ref({
  username: '张三',
  email: 'zhangsan@example.com',
  student_id: 'S10001',
  phone: '',
  bio: '',
  display_name: '',
  campus: ''
})

// 密码修改
const passwordForm = ref({
  old_password: '',
  new_password: '',
  confirm_password: '',
})

// 隐私设置
const privacySettings = ref({
  show_email: false,
  show_phone: false,
  allow_follow: true,
  allow_message: true,
})

// 通知设置
const notificationSettings = ref({
  email_notification: true,
  message_notification: true,
  transaction_notification: true,
  comment_notification: true,
  system_notification: true,
})

const avatarUrl = ref('')

// 加载用户资料
const loadUserProfile = async () => {
  try {
    const response = await api.get('/auth/profile')
    const profile = response.data
    
    profileForm.value = {
      username: '当前用户', // 出于安全考虑不显示真实用户名
      email: '已登录用户', // 出于安全考虑不显示真实邮箱
      student_id: '已认证', // 出于安全考虑不显示真实学号
      phone: profile.phone || '',
      bio: profile.bio || '',
      display_name: profile.display_name || '',
      campus: profile.campus || ''
    }
    
    avatarUrl.value = profile.avatar_url || ''
  } catch (error: any) {
    console.error('加载用户资料失败:', error)
    message.error('加载用户资料失败')
  }
}

const loadUserPreferences = async () => {
  try {
    const { data } = await api.get('/auth/preferences')
    if (data?.privacy) {
      privacySettings.value = {
        ...privacySettings.value,
        ...data.privacy,
      }
    }
    if (data?.notifications) {
      notificationSettings.value = {
        ...notificationSettings.value,
        ...data.notifications,
      }
    }
  } catch (error) {
    console.error('加载偏好设置失败:', error)
    message.error('加载偏好设置失败')
  }
}

const handleAvatarUpload = async (options: { file: UploadFileInfo }) => {
  const file = options.file.file
  if (!file) {
    message.error('请选择文件')
    return
  }
  
  // 检查文件类型
  if (!file.type.startsWith('image/')) {
    message.error('只能上传图片文件')
    return
  }
  
  // 检查文件大小（最大2MB）
  if (file.size > 2 * 1024 * 1024) {
    message.error('图片大小不能超过2MB')
    return
  }
  
  try {
    // 创建 FormData 上传到服务器
    const uploadData = new FormData()
    uploadData.append('file', file)
    
    try {
      const response = await api.post('/upload/avatar', uploadData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      avatarUrl.value = response.data.url
      message.success('头像上传成功')
    } catch (uploadError) {
      // 如果服务器上传失败，使用本地预览
      console.warn('服务器上传失败，使用本地预览')
      avatarUrl.value = URL.createObjectURL(file)
      message.info('已使用本地预览')
    }
  } catch (error) {
    console.error('头像上传失败:', error)
    message.error('头像上传失败')
  }
}

const updateProfile = async () => {
  try {
    await api.put('/auth/profile', {
      display_name: profileForm.value.display_name,
      phone: profileForm.value.phone,
      campus: profileForm.value.campus,
      bio: profileForm.value.bio
    })
    message.success('个人信息更新成功')
  } catch (error: any) {
    message.error(error.response?.data?.detail || '更新失败')
  }
}

const updatePassword = async () => {
  if (passwordForm.value.new_password !== passwordForm.value.confirm_password) {
    message.error('两次输入的密码不一致')
    return
  }
  
  try {
    await api.put('/auth/password', {
      old_password: passwordForm.value.old_password,
      new_password: passwordForm.value.new_password
    })
    message.success('密码修改成功')
    passwordForm.value = {
      old_password: '',
      new_password: '',
      confirm_password: '',
    }
  } catch (error: any) {
    message.error(error.response?.data?.detail || '密码修改失败')
  }
}

const updatePrivacy = async () => {
  try {
    const { data } = await api.put('/auth/preferences/privacy', privacySettings.value)
    privacySettings.value = { ...data }
    message.success('隐私设置已更新')
  } catch (error) {
    message.error('更新失败')
  }
}

const updateNotifications = async () => {
  try {
    const { data } = await api.put('/auth/preferences/notifications', notificationSettings.value)
    notificationSettings.value = { ...data }
    message.success('通知设置已更新')
  } catch (error) {
    message.error('更新失败')
  }
}

// 页面加载时获取用户资料
onMounted(() => {
  loadUserProfile()
  loadUserPreferences()
})
</script>

<template>
  <div class="settings-page">
    <n-card title="账号设置">
      <n-tabs type="line">
        <!-- 个人信息 -->
        <n-tab-pane name="profile" tab="个人信息">
          <n-space vertical :size="24">
            <!-- 头像上传 -->
            <div>
              <div style="margin-bottom: 8px; font-weight: 500">头像</div>
              <n-space align="center">
                <n-avatar :size="80" round>
                  <img v-if="avatarUrl" :src="avatarUrl" />
                  <span v-else>{{ profileForm.username.charAt(0) }}</span>
                </n-avatar>
                <n-upload
                  action="/api/upload/avatar"
                  :custom-request="handleAvatarUpload"
                  :max="1"
                  accept="image/*"
                >
                  <n-button>上传头像</n-button>
                </n-upload>
              </n-space>
            </div>

            <n-form :model="profileForm" label-placement="left" :label-width="100">
              <n-form-item label="显示名称" path="display_name">
                <n-input v-model:value="profileForm.display_name" placeholder="请输入显示名称" />
              </n-form-item>

              <n-form-item label="校区" path="campus">
                <n-input v-model:value="profileForm.campus" placeholder="请输入校区" />
              </n-form-item>

              <n-form-item label="邮箱" path="email">
                <n-input v-model:value="profileForm.email" placeholder="请输入邮箱" disabled />
              </n-form-item>

              <n-form-item label="学号" path="student_id">
                <n-input v-model:value="profileForm.student_id" placeholder="请输入学号" disabled />
              </n-form-item>

              <n-form-item label="手机号" path="phone">
                <n-input v-model:value="profileForm.phone" placeholder="请输入手机号" />
              </n-form-item>

              <n-form-item label="个人简介" path="bio">
                <n-input
                  v-model:value="profileForm.bio"
                  type="textarea"
                  placeholder="介绍一下自己吧"
                  :rows="4"
                />
              </n-form-item>

              <n-form-item>
                <n-button type="primary" @click="updateProfile">保存修改</n-button>
              </n-form-item>
            </n-form>
          </n-space>
        </n-tab-pane>

        <!-- 安全设置 -->
        <n-tab-pane name="security" tab="安全设置">
          <n-form :model="passwordForm" label-placement="left" :label-width="100">
            <n-form-item label="原密码" path="old_password">
              <n-input
                v-model:value="passwordForm.old_password"
                type="password"
                placeholder="请输入原密码"
                show-password-on="click"
              />
            </n-form-item>

            <n-form-item label="新密码" path="new_password">
              <n-input
                v-model:value="passwordForm.new_password"
                type="password"
                placeholder="请输入新密码"
                show-password-on="click"
              />
            </n-form-item>

            <n-form-item label="确认密码" path="confirm_password">
              <n-input
                v-model:value="passwordForm.confirm_password"
                type="password"
                placeholder="请再次输入新密码"
                show-password-on="click"
              />
            </n-form-item>

            <n-form-item>
              <n-button type="primary" @click="updatePassword">修改密码</n-button>
            </n-form-item>
          </n-form>

          <n-divider />

          <div style="padding: 16px 0">
            <h3 style="margin-bottom: 16px">两步验证</h3>
            <p style="color: #666; margin-bottom: 16px">
              启用两步验证后，登录时需要输入验证码，可以大大提高账号安全性
            </p>
            <n-button>启用两步验证</n-button>
          </div>
        </n-tab-pane>

        <!-- 隐私设置 -->
        <n-tab-pane name="privacy" tab="隐私设置">
          <n-form :model="privacySettings" label-placement="left" :label-width="200">
            <n-form-item label="公开邮箱地址">
              <n-switch v-model:value="privacySettings.show_email" />
            </n-form-item>

            <n-form-item label="公开手机号码">
              <n-switch v-model:value="privacySettings.show_phone" />
            </n-form-item>

            <n-form-item label="允许其他用户关注">
              <n-switch v-model:value="privacySettings.allow_follow" />
            </n-form-item>

            <n-form-item label="允许接收私信">
              <n-switch v-model:value="privacySettings.allow_message" />
            </n-form-item>

            <n-form-item>
              <n-button type="primary" @click="updatePrivacy">保存设置</n-button>
            </n-form-item>
          </n-form>
        </n-tab-pane>

        <!-- 通知设置 -->
        <n-tab-pane name="notifications" tab="通知设置">
          <n-form :model="notificationSettings" label-placement="left" :label-width="200">
            <n-form-item label="邮件通知">
              <n-switch v-model:value="notificationSettings.email_notification" />
            </n-form-item>

            <n-form-item label="私信通知">
              <n-switch v-model:value="notificationSettings.message_notification" />
            </n-form-item>

            <n-form-item label="交易通知">
              <n-switch v-model:value="notificationSettings.transaction_notification" />
            </n-form-item>

            <n-form-item label="评论通知">
              <n-switch v-model:value="notificationSettings.comment_notification" />
            </n-form-item>

            <n-form-item label="系统通知">
              <n-switch v-model:value="notificationSettings.system_notification" />
            </n-form-item>

            <n-form-item>
              <n-button type="primary" @click="updateNotifications">保存设置</n-button>
            </n-form-item>
          </n-form>
        </n-tab-pane>

        <!-- 账号管理 -->
        <n-tab-pane name="account" tab="账号管理">
          <n-space vertical :size="24">
            <div>
              <h3 style="color: #f56c6c; margin-bottom: 8px">注销账号</h3>
              <p style="color: #666; margin-bottom: 16px">
                注销账号后，您的所有数据将被永久删除，且无法恢复。请谨慎操作。
              </p>
              <n-button type="error">注销账号</n-button>
            </div>

            <n-divider />

            <div>
              <h3 style="margin-bottom: 8px">导出数据</h3>
              <p style="color: #666; margin-bottom: 16px">
                您可以导出您的个人数据，包括发布的商品、交易记录、消息等。
              </p>
              <n-button>导出我的数据</n-button>
            </div>
          </n-space>
        </n-tab-pane>
      </n-tabs>
    </n-card>
  </div>
</template>

<style scoped>
.settings-page {
  max-width: 900px;
  margin: 0 auto;
  padding: 24px;
}
</style>
