import type {
  PlainTextSourceCreate,
  PlainTextSourceUpdate,
  Source,
  SourceListItem,
} from '@knowledgescope/shared'
import { ApiPaths } from '@knowledgescope/shared'

import { apiRequest } from './http'

// 列出空间下来源（含预览），用在空间详情页来源列表
export function listSources(workspaceId: string): Promise<SourceListItem[]> {
  return apiRequest<SourceListItem[]>(ApiPaths.sources(workspaceId))
}

// 拉取来源全文详情，用在来源抽屉
export function getSource(workspaceId: string, sourceId: string): Promise<Source> {
  return apiRequest<Source>(ApiPaths.source(workspaceId, sourceId))
}

// 创建纯文字来源，用在详情页投递表单
export function createSource(
  workspaceId: string,
  payload: PlainTextSourceCreate,
): Promise<Source> {
  return apiRequest<Source>(ApiPaths.sources(workspaceId), {
    method: 'POST',
    body: payload,
  })
}

// 更新来源标题或正文，用在来源抽屉编辑保存
export function updateSource(
  workspaceId: string,
  sourceId: string,
  payload: PlainTextSourceUpdate,
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
