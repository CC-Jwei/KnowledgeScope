<script setup lang="ts">
import { computed } from 'vue'
import { Connection, RefreshRight } from '@element-plus/icons-vue'

import { useSseHeartbeat } from '@/composables/useSseHeartbeat'
import { formatDateTime } from '@/utils/datetime'

// SSE 心跳订阅状态，用在顶栏徽标
const { connectionState, statusLabel, lastHeartbeatAt, reconnect } = useSseHeartbeat()

// Element Plus tag 类型，用在颜色区分连接态
const tagType = computed(() => {
  if (connectionState.value === 'connected') {
    return 'success'
  }
  if (connectionState.value === 'connecting') {
    return 'warning'
  }
  return 'danger'
})

// 最近心跳可读文案，用在徽标副标题
const heartbeatText = computed(() => {
  if (!lastHeartbeatAt.value) {
    return '尚未收到心跳'
  }
  return `最近心跳 ${formatDateTime(lastHeartbeatAt.value)}`
})
</script>

<template>
  <div class="flex items-center gap-[12px]">
    <div class="flex flex-col items-end gap-[2px]">
      <el-tag :type="tagType" effect="light" round>
        <div class="flex items-center gap-[6px]">
          <el-icon><Connection /></el-icon>
          <div>SSE {{ statusLabel }}</div>
        </div>
      </el-tag>
      <div class="text-xs text-[#8A8A8A]">{{ heartbeatText }}</div>
    </div>
    <el-button
      v-if="connectionState === 'disconnected'"
      size="small"
      :icon="RefreshRight"
      @click="reconnect"
    >
      重连
    </el-button>
  </div>
</template>
