/** 前端展示用常量（非 DTO）。字段契约仍来自 @knowledgescope/shared。 */

// 应用展示名，用在顶栏与页面标题
export const APP_DISPLAY_NAME = '知域 KnowledgeScope'

// 空间名称表单最大长度，对齐 backend workspace_name_max_length，用在创建/编辑校验
export const WORKSPACE_NAME_MAX_LENGTH = 100

// 空间描述表单最大长度，对齐 backend workspace_description_max_length，用在创建/编辑校验
export const WORKSPACE_DESCRIPTION_MAX_LENGTH = 500

// 来源标题表单最大长度，对齐 backend title_max_length，用在投递/编辑校验
export const SOURCE_TITLE_MAX_LENGTH = 200

// 来源正文表单最大长度，对齐 backend content_max_length，用在投递/编辑校验
export const SOURCE_CONTENT_MAX_LENGTH = 100_000

// SSE 连接状态文案，用在顶栏状态徽标
export const SseStatusLabel = {
  Connecting: '连接中',
  Connected: '已连接',
  Disconnected: '已断开',
} as const

export type SseStatusLabelValue = (typeof SseStatusLabel)[keyof typeof SseStatusLabel]
