<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'

import SseStatusBadge from '@/components/SseStatusBadge.vue'
import { APP_DISPLAY_NAME } from '@/constants/ui'
import { authState, clearAuthState } from '@/stores/auth'

// 路由实例，用在导航与退出后跳登录
const router = useRouter()
// 当前路由，用在菜单高亮
const route = useRoute()

// 回到空间列表首页，用在顶栏品牌点击
function goHome(): void {
  void router.push({ name: 'workspace-list' })
}

// 进入模型设置页，用在顶栏入口
function goModelProfiles(): void {
  void router.push({ name: 'model-profiles' })
}

// 清空 Token 并回登录页，用在退出按钮
function handleLogout(): void {
  clearAuthState()
  void router.push({ name: 'login' })
}
</script>

<template>
  <div class="min-h-screen min-w-[800px] bg-[#F5F7FA] text-[#1F1F1F]">
    <header class="border-b border-[#E5E7EB] bg-white">
      <div class="mx-auto flex max-w-[1280px] items-center justify-between gap-[16px] px-[24px] py-[16px]">
        <div class="flex min-w-0 flex-1 items-center gap-[24px]">
          <div class="shrink-0 cursor-pointer transition-colors hover:opacity-80" @click="goHome">
            <div class="text-xl text-[#111827]">{{ APP_DISPLAY_NAME }}</div>
            <div class="text-sm text-[#6B7280]">知识空间 · RAG 入库 · 严格问答</div>
          </div>
          <div class="flex items-center gap-[8px]">
            <div
              class="cursor-pointer rounded-[8px] px-[12px] py-[6px] text-sm transition-colors hover:bg-[#F3F4F6]"
              :class="route.name === 'workspace-list' ? 'bg-[#EEF2FF] text-[#2563EB]' : 'text-[#4B5563]'"
              @click="goHome"
            >
              知识空间
            </div>
            <div
              class="cursor-pointer rounded-[8px] px-[12px] py-[6px] text-sm transition-colors hover:bg-[#F3F4F6]"
              :class="route.name === 'model-profiles' ? 'bg-[#EEF2FF] text-[#2563EB]' : 'text-[#4B5563]'"
              @click="goModelProfiles"
            >
              模型设置
            </div>
          </div>
        </div>
        <div class="flex shrink-0 items-center gap-[16px]">
          <SseStatusBadge />
          <div class="flex flex-col items-end gap-[2px]">
            <div class="text-sm text-[#374151]">{{ authState.user?.phone || '已登录' }}</div>
            <div
              class="cursor-pointer text-xs text-[#6B7280] transition-colors hover:text-[#DC2626]"
              @click="handleLogout"
            >
              退出登录
            </div>
          </div>
        </div>
      </div>
    </header>

    <main class="mx-auto max-w-[1280px] px-[24px] py-[24px]">
      <router-view />
    </main>
  </div>
</template>
