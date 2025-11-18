<template>
  <div class="min-h-screen space-y-6 bg-slate-50 p-6">
    <!-- 页面标题 -->
    <header class="rounded-2xl bg-white p-6 shadow">
      <h1 class="text-2xl font-bold text-slate-900">👥 用户权限管理</h1>
      <p class="mt-2 text-sm text-slate-600">管理用户角色、权限分配、访问控制</p>
    </header>

    <!-- 操作栏 -->
    <section class="flex flex-wrap gap-4">
      <button 
        class="rounded-lg bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700"
        @click="showCreateUserModal = true"
      >
        ➕ 创建用户
      </button>
      <button 
        class="rounded-lg bg-green-600 px-4 py-2 text-sm text-white hover:bg-green-700"
        @click="showCreateRoleModal = true"
      >
        🎭 创建角色
      </button>
      <button 
        class="rounded-lg bg-purple-600 px-4 py-2 text-sm text-white hover:bg-purple-700"
        @click="showPermissionMatrix = !showPermissionMatrix"
      >
        🔐 权限矩阵
      </button>
      <div class="flex-1"></div>
      <input 
        v-model="searchQuery"
        type="text" 
        placeholder="搜索用户..." 
        class="rounded-lg border-2 border-slate-300 px-4 py-2 text-sm focus:border-blue-500 focus:outline-none"
      >
    </section>

    <!-- 用户列表 -->
    <section class="rounded-2xl bg-white p-6 shadow">
      <h2 class="mb-4 text-lg font-semibold text-slate-900">用户列表</h2>
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead class="border-b-2 border-slate-200 bg-slate-50">
            <tr>
              <th class="p-3 text-left text-sm font-semibold">ID</th>
              <th class="p-3 text-left text-sm font-semibold">用户名</th>
              <th class="p-3 text-left text-sm font-semibold">邮箱</th>
              <th class="p-3 text-left text-sm font-semibold">角色</th>
              <th class="p-3 text-left text-sm font-semibold">状态</th>
              <th class="p-3 text-left text-sm font-semibold">创建时间</th>
              <th class="p-3 text-right text-sm font-semibold">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr 
              v-for="user in filteredUsers" 
              :key="user.id"
              class="border-b border-slate-100 hover:bg-slate-50"
            >
              <td class="p-3 text-sm">{{ user.id }}</td>
              <td class="p-3">
                <div class="flex items-center gap-2">
                  <div class="flex h-8 w-8 items-center justify-center rounded-full bg-blue-100 text-sm font-semibold text-blue-600">
                    {{ user.username[0].toUpperCase() }}
                  </div>
                  <span class="font-medium">{{ user.username }}</span>
                </div>
              </td>
              <td class="p-3 text-sm text-slate-600">{{ user.email }}</td>
              <td class="p-3">
                <span 
                  v-for="role in user.roles" 
                  :key="role"
                  class="mr-1 inline-block rounded-full px-2 py-1 text-xs font-semibold"
                  :class="getRoleColor(role)"
                >
                  {{ role }}
                </span>
              </td>
              <td class="p-3">
                <span 
                  class="inline-block rounded-full px-2 py-1 text-xs font-semibold"
                  :class="user.is_active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'"
                >
                  {{ user.is_active ? '活跃' : '禁用' }}
                </span>
              </td>
              <td class="p-3 text-sm text-slate-600">{{ user.created_at }}</td>
              <td class="p-3 text-right">
                <button class="mr-2 text-blue-600 hover:text-blue-800" @click="editUser(user)">编辑</button>
                <button class="text-red-600 hover:text-red-800" @click="deleteUser(user.id)">删除</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- 角色管理 -->
    <section class="grid gap-6 lg:grid-cols-2">
      <article class="rounded-2xl bg-white p-6 shadow">
        <h2 class="mb-4 text-lg font-semibold text-slate-900">角色列表</h2>
        <div class="space-y-3">
          <div 
            v-for="role in roles" 
            :key="role.id"
            class="rounded-lg border-2 border-slate-200 p-4 hover:border-blue-300"
          >
            <div class="flex items-start justify-between">
              <div>
                <h3 class="font-semibold text-slate-900">{{ role.name }}</h3>
                <p class="mt-1 text-sm text-slate-600">{{ role.description }}</p>
                <div class="mt-2 flex flex-wrap gap-1">
                  <span 
                    v-for="perm in role.permissions" 
                    :key="perm"
                    class="rounded bg-slate-100 px-2 py-1 text-xs text-slate-700"
                  >
                    {{ perm }}
                  </span>
                </div>
              </div>
              <button class="text-slate-400 hover:text-slate-600">⚙️</button>
            </div>
          </div>
        </div>
      </article>

      <article class="rounded-2xl bg-white p-6 shadow">
        <h2 class="mb-4 text-lg font-semibold text-slate-900">权限列表</h2>
        <div class="space-y-2">
          <div 
            v-for="permission in permissions" 
            :key="permission.id"
            class="flex items-center justify-between rounded-lg border border-slate-200 p-3"
          >
            <div>
              <p class="font-medium text-slate-900">{{ permission.name }}</p>
              <p class="text-xs text-slate-500">{{ permission.resource }}:{{ permission.action }}</p>
            </div>
            <span class="rounded-full bg-blue-100 px-2 py-1 text-xs font-semibold text-blue-700">
              {{ permission.user_count }} 用户
            </span>
          </div>
        </div>
      </article>
    </section>

    <!-- 权限矩阵 -->
    <section v-if="showPermissionMatrix" class="rounded-2xl bg-white p-6 shadow">
      <h2 class="mb-4 text-lg font-semibold text-slate-900">📊 权限矩阵</h2>
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b-2 border-slate-200 bg-slate-50">
              <th class="p-2 text-left font-semibold">角色 \ 权限</th>
              <th v-for="perm in allPermissions" :key="perm" class="p-2 text-center font-semibold">
                {{ perm }}
              </th>
            </tr>
          </thead>
          <tbody>
            <tr 
              v-for="role in roles" 
              :key="role.id"
              class="border-b border-slate-100"
            >
              <td class="p-2 font-medium">{{ role.name }}</td>
              <td 
                v-for="perm in allPermissions" 
                :key="perm"
                class="p-2 text-center"
              >
                <span v-if="role.permissions.includes(perm)" class="text-green-600">✓</span>
                <span v-else class="text-slate-300">✗</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'

const showCreateUserModal = ref(false)
const showCreateRoleModal = ref(false)
const showPermissionMatrix = ref(false)
const searchQuery = ref('')

// 模拟数据
const users = ref([
  { id: 1, username: 'admin', email: 'admin@csu.edu.cn', roles: ['管理员'], is_active: true, created_at: '2025-01-01' },
  { id: 2, username: 'teacher_zhang', email: 'zhang@csu.edu.cn', roles: ['教师'], is_active: true, created_at: '2025-01-05' },
  { id: 3, username: 'student_li', email: 'li@csu.edu.cn', roles: ['学生'], is_active: true, created_at: '2025-01-10' },
  { id: 4, username: 'moderator', email: 'mod@csu.edu.cn', roles: ['审核员'], is_active: true, created_at: '2025-01-12' },
  { id: 5, username: 'analyst', email: 'analyst@csu.edu.cn', roles: ['分析师', '学生'], is_active: false, created_at: '2025-01-15' }
])

const roles = ref([
  { 
    id: 1, 
    name: '管理员', 
    description: '系统最高权限，可管理所有功能',
    permissions: ['用户管理', '角色管理', '数据库管理', '系统配置', '数据导出']
  },
  { 
    id: 2, 
    name: '教师', 
    description: '可发布商品、查看统计数据',
    permissions: ['商品发布', '订单管理', '数据查看']
  },
  { 
    id: 3, 
    name: '学生', 
    description: '可购买商品、发布二手物品',
    permissions: ['商品浏览', '商品发布', '购买商品']
  },
  { 
    id: 4, 
    name: '审核员', 
    description: '审核用户发布的内容',
    permissions: ['内容审核', '用户封禁', '数据查看']
  }
])

const permissions = ref([
  { id: 1, name: '用户管理', resource: 'users', action: 'manage', user_count: 2 },
  { id: 2, name: '角色管理', resource: 'roles', action: 'manage', user_count: 2 },
  { id: 3, name: '商品发布', resource: 'items', action: 'create', user_count: 156 },
  { id: 4, name: '订单管理', resource: 'transactions', action: 'manage', user_count: 45 },
  { id: 5, name: '数据库管理', resource: 'database', action: 'admin', user_count: 2 },
  { id: 6, name: '系统配置', resource: 'system', action: 'config', user_count: 2 },
  { id: 7, name: '内容审核', resource: 'content', action: 'review', user_count: 8 },
  { id: 8, name: '数据导出', resource: 'data', action: 'export', user_count: 5 }
])

const allPermissions = ref(['用户管理', '角色管理', '商品发布', '订单管理', '数据库管理', '系统配置', '内容审核', '数据导出'])

const filteredUsers = computed(() => {
  if (!searchQuery.value) return users.value
  const query = searchQuery.value.toLowerCase()
  return users.value.filter(u => 
    u.username.toLowerCase().includes(query) || 
    u.email.toLowerCase().includes(query)
  )
})

const getRoleColor = (role: string) => {
  const colors: Record<string, string> = {
    '管理员': 'bg-red-100 text-red-700',
    '教师': 'bg-blue-100 text-blue-700',
    '学生': 'bg-green-100 text-green-700',
    '审核员': 'bg-purple-100 text-purple-700',
    '分析师': 'bg-yellow-100 text-yellow-700'
  }
  return colors[role] || 'bg-slate-100 text-slate-700'
}

const editUser = (user: any) => {
  console.log('编辑用户:', user)
}

const deleteUser = (userId: number) => {
  if (confirm('确定要删除此用户吗?')) {
    users.value = users.value.filter(u => u.id !== userId)
  }
}
</script>
