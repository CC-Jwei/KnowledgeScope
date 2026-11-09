/**
 * Client constants aligned with backend (not DTOs).
 * Domain fields still come from OpenAPI-generated types.
 */

// API v1 前缀，对齐 backend API_V1_PREFIX 默认值，用在路径拼装与请求基址
export const API_V1_PREFIX = '/api/v1' as const

// 健康检查路径（无 API 前缀），用在 front 探活
export const HEALTH_PATH = '/health' as const

// OpenAPI JSON 路径（无 API 前缀），用在调试或本地契约核对
export const OPENAPI_PATH = '/openapi.json' as const

// SSE 事件名，对齐 backend events.py 的 event 字段，用在 EventSource 分支判断
export const SseEventName = {
  Connected: 'connected',
  Heartbeat: 'heartbeat',
} as const

export type SseEventNameValue = (typeof SseEventName)[keyof typeof SseEventName]

// MVP 唯一来源类型字面量，用在创建来源时的类型约定展示
export const MVP_SOURCE_TYPE = 'plain_text' as const

// MVP 创建后来源状态字面量，用在列表状态展示
export const MVP_SOURCE_STATUS = 'ready' as const
