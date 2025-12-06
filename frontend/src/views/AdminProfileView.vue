<template>
  <div class="min-h-screen space-y-6 bg-gradient-to-b from-slate-50 to-white p-6">
    <section class="rounded-3xl bg-white p-6 shadow">
      <header class="flex flex-col gap-2 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <p class="text-xs uppercase tracking-widest text-slate-400">account</p>
          <h1 class="text-3xl font-semibold text-slate-900">管理员个人中心</h1>
          <p class="mt-2 text-sm text-slate-500">
            查看当前登录身份、角色权限与最近活动，快速跳转至系统设置、审计日志等关键页面。
          </p>
        </div>
        <div class="flex flex-wrap gap-3">
          <button
            class="rounded-full bg-indigo-600 px-4 py-2 text-sm text-white shadow hover:bg-indigo-700"
            @click="goSettings"
          >
            ⚙️ 系统设置
          </button>
          <button
            class="rounded-full border border-slate-300 px-4 py-2 text-sm text-slate-700 hover:bg-slate-50"
            @click="logout"
          >
            🚪 退出登录
          </button>
        </div>
      </header>
    </section>

    <section class="grid gap-4 lg:grid-cols-3">
      <article class="rounded-2xl bg-white p-5 shadow">
        <p class="text-xs uppercase text-slate-400">用户名</p>
        <p class="mt-2 text-2xl font-semibold text-slate-900">{{ userName }}</p>
        <p class="mt-1 text-sm text-slate-500">ID: {{ userId }}</p>
      </article>
      <article class="rounded-2xl bg-white p-5 shadow">
        <p class="text-xs uppercase text-slate-400">角色与权限</p>
        <div class="mt-2 flex flex-wrap gap-2">
          <span
            v-for="role in roles"
            :key="role"
            class="rounded-full bg-indigo-50 px-3 py-1 text-xs font-semibold text-indigo-600"
          >
            {{ role }}
          </span>
          <span v-if="roles.length === 0" class="text-sm text-slate-400">暂无角色</span>
        </div>
      </article>
      <article class="rounded-2xl bg-white p-5 shadow">
        <p class="text-xs uppercase text-slate-400">最近登录</p>
        <p class="mt-2 text-xl font-semibold text-slate-900">{{ lastLoginLabel }}</p>
        <p class="mt-1 text-sm text-slate-500">如有异常，可立即修改密码并查看审计日志。</p>
      </article>
    </section>

    <section class="grid gap-4 lg:grid-cols-2">
      <article class="rounded-2xl bg-white p-5 shadow">
        <header class="mb-4 flex items-center justify-between">
          <h2 class="text-lg font-semibold text-slate-900">快速入口</h2>
          <span class="text-xs text-slate-400">常用管理动作</span>
        </header>
        <ul class="space-y-3 text-sm text-slate-600">
          <li class="flex items-center justify-between rounded-lg border border-slate-100 p-3">
            <span>查看系统告警与监控</span>
            <button class="text-indigo-600" @click="goMonitor">前往</button>
          </li>
          <li class="flex items-center justify-between rounded-lg border border-slate-100 p-3">
            <span>管理管理员账号与角色</span>
            <button class="text-indigo-600" @click="goUserAdmin">前往</button>
          </li>
          <li class="flex items-center justify-between rounded-lg border border-slate-100 p-3">
            <span>审计日志与安全事件</span>
            <button class="text-indigo-600" @click="goTables('audit_logs')">前往</button>
          </li>
        </ul>
      </article>

      <article class="rounded-2xl bg-white p-5 shadow">
        <header class="mb-4 flex items-center justify-between">
          <h2 class="text-lg font-semibold text-slate-900">安全建议</h2>
          <span class="text-xs text-emerald-500">实时</span>
        </header>
        <ul class="space-y-3 text-sm text-slate-600">
          <li>• 定期更换管理员密码，启用双重验证。</li>
          <li>• 若检测到异常登录，立即暂停相关账号。</li>
          <li>• 下载日志前请确认设备安全并妥善保管。</li>
        </ul>
      </article>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const userName = computed(() => authStore.displayName || authStore.user?.username || '管理员')
const userId = computed(() => authStore.user?.id ?? '--')
const roles = computed(() => authStore.user?.roles ?? [])
const lastLoginLabel = computed(() => {
  if (!authStore.lastLoginAt) return '尚未记录'
  return new Date(authStore.lastLoginAt).toLocaleString()
})

const goSettings = () => router.push('/admin/settings')
const goMonitor = () => router.push('/admin/sync-monitor')
const goUserAdmin = () => router.push('/admin/users')
const goTables = (key: string) => router.push({ path: '/admin/tables', query: { table: key } })
const logout = () => {
  authStore.logout()
  router.push('/login')
}
</script>
