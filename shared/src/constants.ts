/**
 * Client constants aligned with backend (not DTOs).
 * Domain fields still come from OpenAPI-generated types.
 */

import type { MessageRole, ModelPurpose, SourceStatus, SourceType } from './schema.ts'

// API v1 前缀，对齐 backend API_V1_PREFIX 默认值，用在路径拼装与请求基址
export const API_V1_PREFIX = '/api/v1' as const

// 健康检查路径（无 API 前缀），用在 front 探活
export const HEALTH_PATH = '/health' as const

// OpenAPI JSON 路径（无 API 前缀），用在调试或本地契约核对
export const OPENAPI_PATH = '/openapi.json' as const

// 初期可投递的来源类型字面量，用在来源类型切换与创建请求
export const SourceTypeValue = {
  PlainText: 'plain_text',
  Markdown: 'markdown',
  WebPage: 'web_page',
} as const satisfies Record<string, SourceType>

// 初期允许创建的来源类型列表，用在投递表单的类型选项
export const CREATABLE_SOURCE_TYPES = [
  SourceTypeValue.PlainText,
  SourceTypeValue.Markdown,
  SourceTypeValue.WebPage,
] as const satisfies readonly SourceType[]

// 来源处理状态字面量，用在状态徽标、轮询与 ready 检索提示
export const SourceStatusValue = {
  Pending: 'pending',
  Processing: 'processing',
  Ready: 'ready',
  Failed: 'failed',
} as const satisfies Record<string, SourceStatus>

// 创建来源后的初始状态，用在投递后的即时状态展示
export const INITIAL_SOURCE_STATUS = SourceStatusValue.Pending

// 会话消息角色字面量，用在消息气泡与历史展示
export const MessageRoleValue = {
  User: 'user',
  Assistant: 'assistant',
  System: 'system',
} as const satisfies Record<string, MessageRole>

// 模型配置用途字面量，用在聊天/嵌入模型档分组与筛选
export const ModelPurposeValue = {
  Chat: 'chat',
  Embedding: 'embedding',
} as const satisfies Record<string, ModelPurpose>

// 初期唯一回答模式，用在严格边界问答界面说明
export const ANSWER_MODE_STRICT = 'strict' as const

// 严格边界无证据固定回复，对齐 backend STRICT_NO_EVIDENCE_REPLY，用在空检索提示核对
export const STRICT_NO_EVIDENCE_REPLY = '当前知识空间中未找到相关依据。' as const

// SSE 事件名，对齐 backend events.py 的 event 字段，用在 EventSource 分支判断
export const SseEventName = {
  Connected: 'connected',
  Heartbeat: 'heartbeat',
} as const

export type SseEventNameValue = (typeof SseEventName)[keyof typeof SseEventName]

// EventSource 无法自定义请求头时使用的令牌查询参数，用在 ApiPaths.heartbeat
export const SSE_ACCESS_TOKEN_QUERY_PARAM = 'access_token' as const

/** @deprecated Phase 2 请使用 SourceTypeValue.PlainText。 */
export const MVP_SOURCE_TYPE = SourceTypeValue.PlainText

/** @deprecated Phase 2 创建后为 pending；旧常量仅保留给待迁移的 MVP 展示代码。 */
export const MVP_SOURCE_STATUS = SourceStatusValue.Ready
