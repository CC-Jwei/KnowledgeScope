import type {
  Source,
  SourceCreateInput,
  SourceListItem,
  SourceUpdate,
} from '@knowledgescope/shared'
import { ApiPaths } from '@knowledgescope/shared'

import { apiRequest } from './http'

// 列出空间下来源（含状态与预览），用在详情页列表与轮询
export function listSources(workspaceId: string): Promise<SourceListItem[]> {
  return apiRequest<SourceListItem[]>(ApiPaths.sources(workspaceId))
}

// 拉取来源全文详情，用在来源抽屉
export function getSource(workspaceId: string, sourceId: string): Promise<Source> {
  return apiRequest<Source>(ApiPaths.source(workspaceId, sourceId))
}

// 创建 plain_text / markdown / web_page 来源，用在按类型投递表单
export function createSource(workspaceId: string, payload: SourceCreateInput): Promise<Source> {
  return apiRequest<Source>(ApiPaths.sources(workspaceId), {
    method: 'POST',
    body: payload,
  })
}

// 更新来源标题或正文，用在来源抽屉编辑保存
export function updateSource(
  workspaceId: string,
  sourceId: string,
  payload: SourceUpdate,
): Promise<Source> {
  return apiRequest<Source>(ApiPaths.source(workspaceId, sourceId), {
    method: 'PATCH',
    body: payload,
  })
}

// 删除来源，用在列表/抽屉删除确认
export function deleteSource(workspaceId: string, sourceId: string): Promise<void> {
  return apiRequest<void>(ApiPaths.source(workspaceId, sourceId), {
    method: 'DELETE',
  })
}
