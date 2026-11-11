/**
 * REST / SSE path helpers so front does not scatter magic strings.
 * Shapes match backend routes and OpenAPI paths.
 */

import { API_V1_PREFIX, SSE_ACCESS_TOKEN_QUERY_PARAM } from './constants.ts'

// 拼接 API v1 路径片段，用在 ApiPaths 各方法
function joinApi(...segments: string[]): string {
  // 规范化后的路径尾部，用在最终 URL
  const tail = segments
    .map((part) => part.replace(/^\/+|\/+$/g, ''))
    .filter(Boolean)
    .join('/')
  return `${API_V1_PREFIX}/${tail}`
}

// 给 SSE 地址附加编码后的访问令牌，用在 EventSource 心跳连接
function withAccessToken(path: string, accessToken?: string): string {
  if (!accessToken) {
    return path
  }
  // URL 编码后的令牌查询串，用在心跳地址
  const query = `${SSE_ACCESS_TOKEN_QUERY_PARAM}=${encodeURIComponent(accessToken)}`
  return `${path}?${query}`
}

// REST/SSE 路径工厂，用在 front 的 fetch / EventSource
export const ApiPaths = {
  // 注册地址，用在登录注册页提交新用户
  authRegister: () => joinApi('auth', 'register'),
  // 登录地址，用在登录页获取 accessToken
  authLogin: () => joinApi('auth', 'login'),
  // 当前用户地址，用在前端启动时恢复登录态
  authMe: () => joinApi('auth', 'me'),
  // 知识空间列表与创建地址，用在空间列表页
  workspaces: () => joinApi('workspaces'),
  // 单个知识空间地址，用在空间详情/更新/删除
  workspace: (workspaceId: string) => joinApi('workspaces', workspaceId),
  // 空间下来源列表与创建地址，用在来源投递、列表与状态轮询
  sources: (workspaceId: string) => joinApi('workspaces', workspaceId, 'sources'),
  // 单条来源地址，用在来源详情/更新/删除
  source: (workspaceId: string, sourceId: string) =>
    joinApi('workspaces', workspaceId, 'sources', sourceId),
  // 空间下会话列表与创建地址，用在会话侧栏
  conversations: (workspaceId: string) =>
    joinApi('workspaces', workspaceId, 'conversations'),
  // 单个会话地址，用在会话详情与删除
  conversation: (conversationId: string) => joinApi('conversations', conversationId),
  // 会话提问地址，用在严格边界问答输入框
  conversationMessages: (conversationId: string) =>
    joinApi('conversations', conversationId, 'messages'),
  // 模型配置列表与创建地址，用在模型设置页
  modelProfiles: () => joinApi('model-profiles'),
  // 单个模型配置地址，用在个人档更新与删除
  modelProfile: (profileId: string) => joinApi('model-profiles', profileId),
  // SSE 心跳地址，可附带 accessToken，用在顶栏连接状态
  heartbeat: (accessToken?: string) =>
    withAccessToken(joinApi('events', 'heartbeat'), accessToken),
} as const
