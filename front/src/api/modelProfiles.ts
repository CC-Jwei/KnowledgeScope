import type {
  ModelProfile,
  ModelProfileCreate,
  ModelProfileUpdate,
} from '@knowledgescope/shared'
import { ApiPaths } from '@knowledgescope/shared'

import { apiRequest } from './http'

// 列出系统默认与个人模型档，用在模型设置与问答模型选择
export function listModelProfiles(): Promise<ModelProfile[]> {
  return apiRequest<ModelProfile[]>(ApiPaths.modelProfiles())
}

// 创建个人模型档，用在模型设置对话框
export function createModelProfile(payload: ModelProfileCreate): Promise<ModelProfile> {
  return apiRequest<ModelProfile>(ApiPaths.modelProfiles(), {
    method: 'POST',
    body: payload,
  })
}

// 更新个人模型档，Key 不传则保留，用在模型设置编辑
export function updateModelProfile(
  profileId: string,
  payload: ModelProfileUpdate,
): Promise<ModelProfile> {
  return apiRequest<ModelProfile>(ApiPaths.modelProfile(profileId), {
    method: 'PATCH',
    body: payload,
  })
}

// 删除个人模型档，不可删系统默认，用在模型设置列表
export function deleteModelProfile(profileId: string): Promise<void> {
  return apiRequest<void>(ApiPaths.modelProfile(profileId), {
    method: 'DELETE',
  })
}
