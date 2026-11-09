/**
 * REST / SSE path helpers so front does not scatter magic strings.
 * Shapes match backend routes and OpenAPI paths.
 */

import { API_V1_PREFIX } from './constants'

// 拼接 API v1 路径片段，用在 ApiPaths 各方法
function joinApi(...segments: string[]): string {
  // 规范化后的路径尾部，用在最终 URL
  const tail = segments
    .map((part) => part.replace(/^\/+|\/+$/g, ''))
    .filter(Boolean)
    .join('/')
  return `${API_V1_PREFIX}/${tail}`
}

// REST/SSE 路径工厂，用在 front 的 fetch / EventSource
export const ApiPaths = {
  // 知识空间列表与创建地址，用在空间列表页
  workspaces: () => joinApi('workspaces'),
  // 单个知识空间地址，用在空间详情/更新/删除
  workspace: (workspaceId: string) => joinApi('workspaces', workspaceId),
  // 空间下来源列表与创建地址，用在来源投递与列表
  sources: (workspaceId: string) => joinApi('workspaces', workspaceId, 'sources'),
  // 单条来源地址，用在来源详情/更新/删除
  source: (workspaceId: string, sourceId: string) =>
    joinApi('workspaces', workspaceId, 'sources', sourceId),
  // SSE 心跳地址，用在顶栏连接状态
  heartbeat: () => joinApi('events', 'heartbeat'),
} as const
