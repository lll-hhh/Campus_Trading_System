<template>
  <div class="profile-center min-h-screen bg-[#f4f4f4]">
    <!-- Header Section -->
    <div class="bg-[#2e3235] text-white py-8 mb-8">
      <div class="max-w-7xl mx-auto px-4">
        <h1 class="text-3xl font-black tracking-tighter uppercase italic">
          Account <span class="text-primary">Center</span>
          <span class="block text-sm font-normal tracking-widest mt-1 opacity-60 italic">PHOENIX AUTO PARTS / USER PROFILE</span>
        </h1>
      </div>
    </div>

    <div class="max-w-7xl mx-auto px-4 pb-12">
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <!-- Left Column: User Info -->
        <div class="lg:col-span-1 space-y-8">
          <div class="bg-white border border-gray-200 p-8 text-center">
            <div class="w-32 h-32 bg-[#2e3235] rounded-full mx-auto mb-6 flex items-center justify-center text-4xl font-black text-primary italic border-4 border-primary/20">
              {{ displayName ? displayName.charAt(0).toUpperCase() : 'P' }}
            </div>
            <h2 class="text-2xl font-black uppercase italic tracking-tighter mb-2">
              {{ displayName || 'Guest User' }}
            </h2>
            <div class="flex flex-wrap justify-center gap-2 mb-6">
              <span v-for="role in roles" :key="role" class="bg-primary text-white text-[10px] font-bold px-3 py-1 uppercase tracking-widest italic">
                {{ role }}
              </span>
            </div>
            <div class="pt-6 border-t border-gray-100 text-left space-y-4">
              <div class="flex justify-between items-center">
                <span class="text-[10px] font-bold text-gray-400 uppercase tracking-widest">Last Login</span>
                <span class="text-xs font-bold">{{ lastLoginAt ? formatDate(lastLoginAt) : 'Never' }}</span>
              </div>
            </div>
          </div>

          <div class="bg-[#2e3235] text-white p-8">
            <h3 class="text-lg font-black uppercase italic tracking-tighter mb-4 text-primary">System Status</h3>
            <div class="space-y-3">
              <div class="flex items-center gap-3 text-xs font-bold uppercase tracking-widest opacity-60">
                <span class="w-2 h-2 bg-green-500 rounded-full"></span>
                JWT Authentication Active
              </div>
              <div class="flex items-center gap-3 text-xs font-bold uppercase tracking-widest opacity-60">
                <span class="w-2 h-2 bg-green-500 rounded-full"></span>
                Cloud Sync Enabled
              </div>
              <div class="flex items-center gap-3 text-xs font-bold uppercase tracking-widest opacity-60">
                <span class="w-2 h-2 bg-green-500 rounded-full"></span>
                AI Pricing Engine Online
              </div>
            </div>
          </div>
        </div>

        <!-- Right Column: Panels -->
        <div class="lg:col-span-2 space-y-8">
          <div class="bg-white border border-gray-200 p-8">
            <h2 class="text-xl font-black uppercase italic tracking-tighter mb-6 flex items-center gap-2">
              <span class="w-2 h-6 bg-primary"></span>
              Authentication & Security
            </h2>
            <AuthPanel />
          </div>

          <div class="bg-white border border-gray-200 p-8">
            <h2 class="text-xl font-black uppercase italic tracking-tighter mb-6 flex items-center gap-2">
              <span class="w-2 h-6 bg-primary"></span>
              AI Assistant
            </h2>
            <AIChatBox />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import AIChatBox from '@/components/AIChatBox.vue';
import AuthPanel from '@/components/AuthPanel.vue';
import { useAuthStore } from '@/stores/auth';

const authStore = useAuthStore();

const displayName = computed(() => authStore.displayName);
const roles = computed(() => authStore.roles);
const lastLoginAt = computed(() => authStore.lastLoginAt);

function formatDate(input: string | null) {
  if (!input) return '—';
  return new Date(input).toLocaleString();
}
</script>
