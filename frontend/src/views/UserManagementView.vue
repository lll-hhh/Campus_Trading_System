<template>
  <div class="min-h-screen space-y-6 bg-slate-50 p-6">
    <header class="rounded-2xl bg-white p-6 shadow">
      <h1 class="text-2xl font-bold text-slate-900">👥 用户权限管理</h1>
      <p class="mt-2 text-sm text-slate-600">管理用户角色、权限分配、访问控制</p>
    </header>

    <section class="flex flex-wrap gap-4">
      <button
        class="rounded-lg bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700"
        @click="openUserModal()"
      >
        ➕ 创建用户
      </button>
      <button
        class="rounded-lg bg-green-600 px-4 py-2 text-sm text-white hover:bg-green-700"
        @click="openRoleModal()"
      >
        🎭 创建角色
      </button>
      <button
        class="rounded-lg bg-purple-600 px-4 py-2 text-sm text-white hover:bg-purple-700"
        @click="showPermissionMatrix = !showPermissionMatrix"
      >
        🔐 权限矩阵
      </button>
      <div class="flex-1" />
      <input
        v-model="searchQuery"
        type="text"
        placeholder="搜索用户..."
        class="rounded-lg border-2 border-slate-300 px-4 py-2 text-sm focus:border-blue-500 focus:outline-none"
      >
    </section>

    <section class="rounded-2xl bg-white p-6 shadow">
      <div class="mb-4 flex items-center justify-between">
        <h2 class="text-lg font-semibold text-slate-900">用户列表</h2>
        <span class="text-sm text-slate-500">共 {{ users.length }} 人</span>
      </div>
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
                    {{ user.username[0]?.toUpperCase() }}
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
                <button class="mr-2 text-blue-600 hover:text-blue-800" @click="openUserModal(user)">编辑</button>
                <button class="text-red-600 hover:text-red-800" :disabled="deletingUserId === user.id" @click="deleteUser(user.id)">
                  {{ deletingUserId === user.id ? '删除中...' : '删除' }}
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <section class="grid gap-6 lg:grid-cols-2">
      <article class="rounded-2xl bg-white p-6 shadow">
        <h2 class="mb-4 text-lg font-semibold text-slate-900">角色列表</h2>
        <div class="space-y-3">
          <div
            v-for="role in roles"
            :key="role.id"
            class="rounded-lg border-2 border-slate-200 p-4 hover:border-blue-300"
          >
            <div class="flex items-start justify-between gap-3">
              <div>
                <h3 class="font-semibold text-slate-900">{{ role.name }}</h3>
                <p class="mt-1 text-sm text-slate-600">{{ role.description || '暂无描述' }}</p>
                <div class="mt-2 flex flex-wrap gap-1">
                  <span
                    v-for="perm in role.permissions"
                    :key="perm.id"
                    class="rounded bg-slate-100 px-2 py-1 text-xs text-slate-700"
                  >
                    {{ perm.name }}
                  </span>
                </div>
              </div>
              <div class="flex gap-2 text-sm text-slate-500">
                <button class="text-blue-600 hover:text-blue-800" @click="openRoleModal(role)">编辑</button>
                <button class="text-red-600 hover:text-red-800" @click="deleteRole(role.id)">删除</button>
              </div>
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
              <p v-if="permission.description" class="text-xs text-slate-400">{{ permission.description }}</p>
            </div>
            <span class="rounded-full bg-blue-100 px-2 py-1 text-xs font-semibold text-blue-700">
              {{ permission.role_count ?? 0 }} 角色使用
            </span>
          </div>
        </div>
      </article>
    </section>

    <section v-if="showPermissionMatrix" class="rounded-2xl bg-white p-6 shadow">
      <div class="mb-4 flex items-center justify-between">
        <h2 class="text-lg font-semibold text-slate-900">📊 权限矩阵</h2>
        <p class="text-sm text-slate-500">点击复选框可直接配置，右侧按钮保存</p>
      </div>
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b-2 border-slate-200 bg-slate-50">
              <th class="p-2 text-left font-semibold">角色 \ 权限</th>
              <th
                v-for="perm in permissions"
                :key="perm.id"
                class="min-w-[140px] p-2 text-center font-semibold"
              >
                <div class="font-semibold">{{ perm.name }}</div>
                <div class="text-[11px] text-slate-400">{{ perm.resource }}:{{ perm.action }}</div>
              </th>
              <th class="w-24 p-2 text-center font-semibold">操作</th>
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
                v-for="perm in permissions"
                :key="perm.id"
                class="p-2 text-center"
              >
                <input
                  type="checkbox"
                  class="h-4 w-4"
                  :checked="hasPermission(role.id, perm.id)"
                  @change="toggleRolePermission(role.id, perm.id)"
                >
              </td>
              <td class="p-2 text-center">
                <button
                  class="rounded bg-blue-600 px-3 py-1 text-xs text-white disabled:opacity-60"
                  :disabled="rolePermissionSaving[role.id]"
                  @click="saveRolePermissions(role.id)"
                >
                  {{ rolePermissionSaving[role.id] ? '保存中...' : '保存' }}
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <div
      v-if="showCreateUserModal"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4"
    >
      <div class="w-full max-w-xl rounded-2xl bg-white p-6 shadow-xl">
        <div class="mb-4 flex items-center justify-between">
          <h3 class="text-xl font-semibold text-slate-900">{{ isEditingUser ? '编辑用户' : '创建用户' }}</h3>
          <button class="text-slate-400 hover:text-slate-600" @click="closeUserModal">✕</button>
        </div>
        <form class="space-y-4" @submit.prevent="handleSaveUser">
          <div>
            <label class="block text-sm font-medium text-slate-700">用户名</label>
            <input v-model="userForm.username" required type="text" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 focus:border-blue-500 focus:outline-none">
          </div>
          <div>
            <label class="block text-sm font-medium text-slate-700">邮箱</label>
            <input v-model="userForm.email" required type="email" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 focus:border-blue-500 focus:outline-none">
          </div>
          <div>
            <label class="block text-sm font-medium text-slate-700">密码</label>
            <input
              v-model="userForm.password"
              :required="!isEditingUser"
              type="password"
              placeholder="至少 6 位"
              class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 focus:border-blue-500 focus:outline-none"
            >
            <p class="mt-1 text-xs text-slate-500" v-if="isEditingUser">留空表示不修改密码</p>
          </div>
          <div class="grid gap-4 md:grid-cols-2">
            <label class="flex items-center gap-2 text-sm text-slate-700">
              <input type="checkbox" v-model="userForm.is_active" class="h-4 w-4">
              启用账号
            </label>
            <label class="flex items-center gap-2 text-sm text-slate-700">
              <input type="checkbox" v-model="userForm.is_verified" class="h-4 w-4">
              已实名认证
            </label>
          </div>
          <div>
            <label class="block text-sm font-medium text-slate-700">角色</label>
            <select
              v-model="userForm.role_ids"
              multiple
              class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 focus:border-blue-500 focus:outline-none"
            >
              <option v-for="role in roles" :key="role.id" :value="role.id">{{ role.name }}</option>
            </select>
            <p class="mt-1 text-xs text-slate-500">按 Ctrl / Command 可多选</p>
          </div>
          <div class="flex justify-end gap-3">
            <button type="button" class="rounded-lg border border-slate-200 px-4 py-2 text-sm text-slate-700" @click="closeUserModal">取消</button>
            <button type="submit" class="rounded-lg bg-blue-600 px-4 py-2 text-sm text-white disabled:opacity-60" :disabled="savingUser">
              {{ savingUser ? '保存中...' : '保存' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <div
      v-if="showCreateRoleModal"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4"
    >
      <div class="w-full max-w-xl rounded-2xl bg-white p-6 shadow-xl">
        <div class="mb-4 flex items-center justify-between">
          <h3 class="text-xl font-semibold text-slate-900">{{ isEditingRole ? '编辑角色' : '创建角色' }}</h3>
          <button class="text-slate-400 hover:text-slate-600" @click="closeRoleModal">✕</button>
        </div>
        <form class="space-y-4" @submit.prevent="handleSaveRole">
          <div>
            <label class="block text-sm font-medium text-slate-700">角色名称</label>
            <input v-model="roleForm.name" required type="text" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 focus:border-blue-500 focus:outline-none">
          </div>
          <div>
            <label class="block text-sm font-medium text-slate-700">描述</label>
            <textarea v-model="roleForm.description" rows="3" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 focus:border-blue-500 focus:outline-none" />
          </div>
          <div>
            <label class="block text-sm font-medium text-slate-700">权限</label>
            <select
              v-model="roleForm.permission_ids"
              multiple
              class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 focus:border-blue-500 focus:outline-none"
            >
              <option v-for="perm in permissions" :key="perm.id" :value="perm.id">
                {{ perm.name }} ({{ perm.resource }}:{{ perm.action }})
              </option>
            </select>
          </div>
          <div class="flex justify-end gap-3">
            <button type="button" class="rounded-lg border border-slate-200 px-4 py-2 text-sm text-slate-700" @click="closeRoleModal">取消</button>
            <button type="submit" class="rounded-lg bg-green-600 px-4 py-2 text-sm text-white disabled:opacity-60" :disabled="savingRole">
              {{ savingRole ? '保存中...' : '保存' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useMessage } from 'naive-ui'

import { http } from '@/lib/http'

interface AdminPermission {
  id: number
  name: string
  resource: string
  action: string
  description?: string | null
  role_count?: number
}

interface AdminRole {
  id: number
  name: string
  description?: string | null
  permissions: AdminPermission[]
  permission_ids: number[]
}

interface AdminUser {
  id: number
  username: string
  email: string
  roles: string[]
  role_ids: number[]
  is_active: boolean
  is_verified: boolean
  created_at?: string | null
}

type RolePermissionState = Record<number, Set<number>>

const message = useMessage()
const loading = ref(false)

const showCreateUserModal = ref(false)
const showCreateRoleModal = ref(false)
const showPermissionMatrix = ref(false)
const searchQuery = ref('')

const users = ref<AdminUser[]>([])
const roles = ref<AdminRole[]>([])
const permissions = ref<AdminPermission[]>([])

const deletingUserId = ref<number | null>(null)
const savingUser = ref(false)
const savingRole = ref(false)
const isEditingUser = ref(false)
const isEditingRole = ref(false)

const userForm = ref({
  id: null as number | null,
  username: '',
  email: '',
  password: '',
  is_active: true,
  is_verified: false,
  role_ids: [] as Array<number | string>,
})

const roleForm = ref({
  id: null as number | null,
  name: '',
  description: '' as string | null,
  permission_ids: [] as Array<number | string>,
})

const rolePermissionDraft = ref<RolePermissionState>({})
const rolePermissionSaving = ref<Record<number, boolean>>({})

const filteredUsers = computed(() => {
  if (!searchQuery.value) return users.value
  const query = searchQuery.value.toLowerCase()
  return users.value.filter((u) =>
    u.username.toLowerCase().includes(query) ||
    u.email.toLowerCase().includes(query)
  )
})

const syncRolePermissionDraft = () => {
  const draft: RolePermissionState = {}
  roles.value.forEach((role) => {
    draft[role.id] = new Set(role.permission_ids)
  })
  rolePermissionDraft.value = draft
}

watch(roles, syncRolePermissionDraft, { immediate: true })

const hasPermission = (roleId: number, permissionId: number) => {
  return rolePermissionDraft.value[roleId]?.has(permissionId) ?? false
}

const toggleRolePermission = (roleId: number, permissionId: number) => {
  const current = rolePermissionDraft.value[roleId] ?? new Set<number>()
  if (current.has(permissionId)) {
    current.delete(permissionId)
  } else {
    current.add(permissionId)
  }
  rolePermissionDraft.value[roleId] = current
}

const getRoleColor = (role: string) => {
  const colors: Record<string, string> = {
    管理员: 'bg-red-100 text-red-700',
    admin: 'bg-red-100 text-red-700',
    教师: 'bg-blue-100 text-blue-700',
    学生: 'bg-green-100 text-green-700',
    用户: 'bg-green-100 text-green-700',
    审核员: 'bg-purple-100 text-purple-700',
    分析师: 'bg-yellow-100 text-yellow-700',
  }
  return colors[role] || 'bg-slate-100 text-slate-700'
}

const loadUsers = async () => {
  const { data } = await http.get('/admin/users', { params: { page: 1, page_size: 200 } })
  const rows: AdminUser[] = data.items ?? []
  users.value = rows.map((u) => ({
    ...u,
    created_at: u.created_at ? new Date(u.created_at).toLocaleString() : '-',
  }))
}

const loadRoles = async () => {
  const { data } = await http.get('/admin/roles')
  roles.value = data as AdminRole[]
}

const loadPermissions = async () => {
  const { data } = await http.get('/admin/permissions')
  permissions.value = data as AdminPermission[]
}

const openUserModal = (user?: AdminUser) => {
  if (user) {
    isEditingUser.value = true
    userForm.value = {
      id: user.id,
      username: user.username,
      email: user.email,
      password: '',
      is_active: user.is_active,
      is_verified: user.is_verified,
      role_ids: [...user.role_ids],
    }
  } else {
    isEditingUser.value = false
    userForm.value = {
      id: null,
      username: '',
      email: '',
      password: '',
      is_active: true,
      is_verified: false,
      role_ids: [],
    }
  }
  showCreateUserModal.value = true
}

const closeUserModal = () => {
  showCreateUserModal.value = false
  savingUser.value = false
  isEditingUser.value = false
}

const handleSaveUser = async () => {
  savingUser.value = true
  const payload = {
    username: userForm.value.username.trim(),
    email: userForm.value.email.trim(),
    is_active: userForm.value.is_active,
    is_verified: userForm.value.is_verified,
    role_ids: userForm.value.role_ids.map((id) => Number(id)),
  } as Record<string, unknown>

  if (!isEditingUser.value || userForm.value.password) {
    payload.password = userForm.value.password
  }

  try {
    if (isEditingUser.value && userForm.value.id) {
      await http.put(`/admin/users/${userForm.value.id}`, payload)
      message.success('用户信息已更新')
    } else {
      await http.post('/admin/users', payload)
      message.success('用户创建成功')
    }
    await loadUsers()
    closeUserModal()
  } finally {
    savingUser.value = false
  }
}

const deleteUser = async (userId: number) => {
  if (!confirm('确定要删除此用户吗？')) return
  deletingUserId.value = userId
  try {
    await http.delete(`/admin/users/${userId}`)
    users.value = users.value.filter((user) => user.id !== userId)
    message.success('用户删除成功')
  } finally {
    deletingUserId.value = null
  }
}

const openRoleModal = (role?: AdminRole) => {
  if (role) {
    isEditingRole.value = true
    roleForm.value = {
      id: role.id,
      name: role.name,
      description: role.description ?? '',
      permission_ids: [...role.permission_ids],
    }
  } else {
    isEditingRole.value = false
    roleForm.value = {
      id: null,
      name: '',
      description: '',
      permission_ids: [],
    }
  }
  showCreateRoleModal.value = true
}

const closeRoleModal = () => {
  showCreateRoleModal.value = false
  savingRole.value = false
  isEditingRole.value = false
}

const handleSaveRole = async () => {
  savingRole.value = true
  const payload = {
    name: roleForm.value.name.trim(),
    description: roleForm.value.description?.trim() || null,
    permission_ids: roleForm.value.permission_ids.map((id) => Number(id)),
  }
  try {
    if (isEditingRole.value && roleForm.value.id) {
      await http.put(`/admin/roles/${roleForm.value.id}`, payload)
      message.success('角色已更新')
    } else {
      await http.post('/admin/roles', payload)
      message.success('角色已创建')
    }
    await loadRoles()
    await loadUsers()
    closeRoleModal()
  } finally {
    savingRole.value = false
  }
}

const deleteRole = async (roleId: number) => {
  if (!confirm('确定要删除此角色吗？删除后关联用户将失去该角色。')) return
  try {
    await http.delete(`/admin/roles/${roleId}`)
    roles.value = roles.value.filter((role) => role.id !== roleId)
    await loadUsers()
    message.success('角色已删除')
  } catch (error) {
    // handled globally
  }
}

const saveRolePermissions = async (roleId: number) => {
  const permissionSet = rolePermissionDraft.value[roleId] ?? new Set<number>()
  rolePermissionSaving.value = { ...rolePermissionSaving.value, [roleId]: true }
  try {
    await http.put(`/admin/roles/${roleId}/permissions`, {
      permission_ids: Array.from(permissionSet.values()),
    })
    await loadRoles()
    message.success('权限矩阵已保存')
  } finally {
    rolePermissionSaving.value = { ...rolePermissionSaving.value, [roleId]: false }
  }
}

const initialize = async () => {
  loading.value = true
  try {
    await Promise.all([loadUsers(), loadRoles(), loadPermissions()])
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  initialize()
})
</script>
