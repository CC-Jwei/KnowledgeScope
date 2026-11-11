import type {
  AskMessageRequest,
  AskMessageResponse,
  Conversation,
  ConversationCreate,
  ConversationDetail,
} from '@knowledgescope/shared'
import { ApiPaths } from '@knowledgescope/shared'

import { apiRequest } from './http'

// 列出空间下会话，用在会话侧栏
export function listConversations(workspaceId: string): Promise<Conversation[]> {
  return apiRequest<Conversation[]>(ApiPaths.conversations(workspaceId))
}

// 创建会话，用在「新建会话」按钮
export function createConversation(
  workspaceId: string,
  payload: ConversationCreate,
): Promise<Conversation> {
  return apiRequest<Conversation>(ApiPaths.conversations(workspaceId), {
    method: 'POST',
    body: payload,
  })
}

// 拉取含消息的会话详情，用在会话主区
export function getConversation(conversationId: string): Promise<ConversationDetail> {
  return apiRequest<ConversationDetail>(ApiPaths.conversation(conversationId))
}

// 删除会话与消息，用在侧栏删除确认
export function deleteConversation(conversationId: string): Promise<void> {
  return apiRequest<void>(ApiPaths.conversation(conversationId), {
    method: 'DELETE',
  })
}

// 严格边界提问并返回答案与引用，用在输入框发送
export function askMessage(
  conversationId: string,
  payload: AskMessageRequest,
): Promise<AskMessageResponse> {
  return apiRequest<AskMessageResponse>(ApiPaths.conversationMessages(conversationId), {
    method: 'POST',
    body: payload,
  })
}
