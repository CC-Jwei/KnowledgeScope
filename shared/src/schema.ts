/**
 * Friendly aliases projected from generated OpenAPI types.
 * Do not hand-write conflicting fields; change backend Pydantic, then regenerate.
 */

import type { components, operations, paths } from '../generated/openapi.ts'

export type { components, operations, paths }

export type Schemas = components['schemas']

/** Auth */
export type RegisterRequest = Schemas['RegisterRequest']
export type LoginRequest = Schemas['LoginRequest']
export type TokenResponse = Schemas['TokenResponse']
export type UserPublic = Schemas['UserPublic']

/** Workspace */
export type Workspace = Schemas['Workspace']
export type WorkspaceCreate = Schemas['WorkspaceCreate']
export type WorkspaceUpdate = Schemas['WorkspaceUpdate']

/** Source */
export type Source = Schemas['Source']
export type SourceListItem = Schemas['SourceListItem']
export type SourceCreate = Schemas['SourceCreate']
export type SourceUpdate = Schemas['SourceUpdate']
export type SourceType = Schemas['SourceType']
export type SourceStatus = Schemas['SourceStatus']

// 文本类来源创建输入，收窄 OpenAPI 无法表达的 content 条件必填，用在来源投递表单
export type TextContentSourceCreate<T extends 'plain_text' | 'markdown'> = Omit<
  SourceCreate,
  'type' | 'content'
> & {
  type: T
  content: string
}

// 纯文字创建输入，用在 plain_text 投递表单
export type PlainTextSourceCreate = TextContentSourceCreate<'plain_text'>

// Markdown 创建输入，用在 markdown 投递表单
export type MarkdownSourceCreate = TextContentSourceCreate<'markdown'>

// 网页创建输入，收窄 OpenAPI 无法表达的 url 条件必填，用在 web_page 投递表单
export type WebPageSourceCreate = Omit<SourceCreate, 'type' | 'url'> & {
  type: 'web_page'
  url: string
}

// 三种初期来源的创建输入联合，用在按类型切换的来源投递表单
export type SourceCreateInput =
  | PlainTextSourceCreate
  | MarkdownSourceCreate
  | WebPageSourceCreate

/** @deprecated Phase 2 统一使用 SourceUpdate；保留别名供旧调用处迁移。 */
export type PlainTextSourceUpdate = SourceUpdate

/** Conversation and strict-boundary ask */
export type Citation = Schemas['Citation']
export type MessageRole = Schemas['MessageRole']
export type Message = Schemas['Message']
export type Conversation = Schemas['Conversation']
export type ConversationCreate = Schemas['ConversationCreate']
export type ConversationDetail = Schemas['ConversationDetail']
export type AskMessageRequest = Schemas['AskMessageRequest']
export type AskMessageResponse = Schemas['AskMessageResponse']

/** Model profiles */
export type ModelPurpose = Schemas['ModelPurpose']
export type ModelProfile = Schemas['ModelProfile']
export type ModelProfileCreate = Schemas['ModelProfileCreate']
export type ModelProfileUpdate = Schemas['ModelProfileUpdate']

/** SSE event data (explicitly mounted in OpenAPI components) */
export type ConnectedEvent = Schemas['ConnectedEvent']
export type HeartbeatEvent = Schemas['HeartbeatEvent']

/** FastAPI validation error body */
export type HTTPValidationError = Schemas['HTTPValidationError']
export type ValidationError = Schemas['ValidationError']
