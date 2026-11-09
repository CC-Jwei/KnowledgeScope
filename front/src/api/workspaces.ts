import type { Workspace, WorkspaceCreate, WorkspaceUpdate } from '@knowledgescope/shared'
import { ApiPaths } from '@knowledgescope/shared'

import { apiRequest } from './http'

// 拉取知识空间列表，用在空间列表页
export function listWorkspaces(): Promise<Workspace[]> {
  return apiRequest<Workspace[]>(ApiPaths.workspaces())
}

// 按 id 拉取知识空间详情，用在空间详情页头信息
export function getWorkspace(workspaceId: string): Promise<Workspace> {
  return apiRequest<Workspace>(ApiPaths.workspace(workspaceId))
}

// 创建知识空间，用在列表页新建对话框
export function createWorkspace(payload: WorkspaceCreate): Promise<Workspace> {
  return apiRequest<Workspace>(ApiPaths.workspaces(), {
    method: 'POST',
    body: payload,
  })
}

// 更新知识空间名称或描述，用在详情页编辑
export function updateWorkspace(
  workspaceId: string,
  payload: WorkspaceUpdate,
): Promise<Workspace> {
  return apiRequest<Workspace>(ApiPaths.workspace(workspaceId), {
    method: 'PATCH',
    body: payload,
  })
}

// 删除知识空间（级联删除来源），用在列表/详情删除确认
export function deleteWorkspace(workspaceId: string): Promise<void> {
  return apiRequest<void>(ApiPaths.workspace(workspaceId), {
    method: 'DELETE',
  })
}
