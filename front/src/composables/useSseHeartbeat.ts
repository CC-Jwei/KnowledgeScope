import { onMounted, onUnmounted, ref } from 'vue'

import type { ConnectedEvent, HeartbeatEvent } from '@knowledgescope/shared'
import { ApiPaths, SseEventName } from '@knowledgescope/shared'

import { buildApiUrl } from '@/api/http'
import { SseStatusLabel, type SseStatusLabelValue } from '@/constants/ui'

export type SseConnectionState = 'connecting' | 'connected' | 'disconnected'

// 订阅后端 SSE 心跳并暴露连接状态，用在顶栏 SseStatusBadge
export function useSseHeartbeat() {
  // 当前连接态，用在徽标颜色与文案
  const connectionState = ref<SseConnectionState>('connecting')
  // 最近一次心跳 ISO 时间，用在徽标副文案
  const lastHeartbeatAt = ref<string | null>(null)
  // 最近一次 connected 消息，用在调试展示
  const lastConnectedMessage = ref<string | null>(null)
  // EventSource 实例，用在重连与卸载关闭
  let eventSource: EventSource | null = null
  // 延迟重连定时器，用在断开后自动恢复
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null
  // 组件是否仍挂载，用在避免卸载后重连
  let alive = true

  // 把内部状态映射成中文标签，用在顶栏展示
  const statusLabel = ref<SseStatusLabelValue>(SseStatusLabel.Connecting)

  // 同步 statusLabel，用在 connectionState 变更后
  function syncLabel(state: SseConnectionState): void {
    if (state === 'connecting') {
      statusLabel.value = SseStatusLabel.Connecting
      return
    }
    if (state === 'connected') {
      statusLabel.value = SseStatusLabel.Connected
      return
    }
    statusLabel.value = SseStatusLabel.Disconnected
  }

  // 清理重连定时器，用在重新连接与卸载
  function clearReconnectTimer(): void {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
  }

  // 关闭现有 EventSource，用在重连前与卸载
  function closeEventSource(): void {
    if (eventSource) {
      eventSource.close()
      eventSource = null
    }
  }

  // 安排一次延迟重连，用在 onerror
  function scheduleReconnect(): void {
    if (!alive) {
      return
    }
    clearReconnectTimer()
    connectionState.value = 'disconnected'
    syncLabel('disconnected')
    reconnectTimer = setTimeout(() => {
      connect()
    }, 3000)
  }

  // 建立 SSE 连接并绑定事件，用在挂载与重连
  function connect(): void {
    if (!alive) {
      return
    }

    clearReconnectTimer()
    closeEventSource()
    connectionState.value = 'connecting'
    syncLabel('connecting')

    // 同源或代理后的心跳 URL，用在 EventSource
    const url = buildApiUrl(ApiPaths.heartbeat())
    eventSource = new EventSource(url)

    eventSource.addEventListener(SseEventName.Connected, (event: MessageEvent<string>) => {
      try {
        // connected 事件载荷，用在记录服务端问候
        const data = JSON.parse(event.data) as ConnectedEvent
        lastConnectedMessage.value = data.message
      } catch {
        lastConnectedMessage.value = event.data
      }
      connectionState.value = 'connected'
      syncLabel('connected')
    })

    eventSource.addEventListener(SseEventName.Heartbeat, (event: MessageEvent<string>) => {
      try {
        // heartbeat 事件载荷，用在更新最近心跳时间
        const data = JSON.parse(event.data) as HeartbeatEvent
        lastHeartbeatAt.value = data.ts || data.serverTime || null
      } catch {
        lastHeartbeatAt.value = new Date().toISOString()
      }
      connectionState.value = 'connected'
      syncLabel('connected')
    })

    eventSource.onerror = () => {
      closeEventSource()
      scheduleReconnect()
    }
  }

  // 主动断开并停止重连，用在组件卸载
  function disconnect(): void {
    alive = false
    clearReconnectTimer()
    closeEventSource()
    connectionState.value = 'disconnected'
    syncLabel('disconnected')
  }

  onMounted(() => {
    alive = true
    connect()
  })

  onUnmounted(() => {
    disconnect()
  })

  return {
    connectionState,
    statusLabel,
    lastHeartbeatAt,
    lastConnectedMessage,
    reconnect: connect,
    disconnect,
  }
}
