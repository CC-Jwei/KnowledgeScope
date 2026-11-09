<script setup lang="ts">
import { useRouter } from 'vue-router'

import SseStatusBadge from '@/components/SseStatusBadge.vue'
import { APP_DISPLAY_NAME } from '@/constants/ui'

// 路由实例，用在点击品牌回列表
const router = useRouter()

// 回到空间列表首页，用在顶栏品牌点击
function goHome(): void {
  void router.push({ name: 'workspace-list' })
}
</script>

<template>
  <div class="min-h-screen min-w-[800px] bg-[#F5F7FA] text-[#1F1F1F]">
    <header class="border-b border-[#E5E7EB] bg-white">
      <div class="mx-auto flex max-w-[1200px] items-center justify-between px-[24px] py-[16px]">
        <div
          class="cursor-pointer transition-colors hover:opacity-80"
          @click="goHome"
        >
          <div class="text-xl text-[#111827]">{{ APP_DISPLAY_NAME }}</div>
          <div class="text-sm text-[#6B7280]">知识空间 · 纯文字来源 · SSE 心跳</div>
        </div>
        <SseStatusBadge />
      </div>
    </header>

    <main class="mx-auto max-w-[1200px] px-[24px] py-[24px]">
      <router-view />
    </main>
  </div>
</template>
