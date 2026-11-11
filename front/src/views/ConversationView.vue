<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, Delete, Plus, Promotion } from '@element-plus/icons-vue'

import type {
  AskMessageRequest,
  Conversation,
  ConversationDetail,
  Message,
  ModelProfile,
} from '@knowledgescope/shared'
import {
  ANSWER_MODE_STRICT,
  ModelPurposeValue,
  SourceStatusValue,
} from '@knowledgescope/shared'

import { listSources } from '@/api/sources'
import { getWorkspace } from '@/api/workspaces'
import {
  askMessage,
  createConversation,
  deleteConversation,
  getConversation,
  listConversations,
} from '@/api/conversations'
import { listModelProfiles } from '@/api/modelProfiles'
import type { Workspace } from '@knowledgescope/shared'
import { SOURCE_STATUS_LABEL } from '@/utils/sourceStatus'
import { formatDateTime } from '@/utils/datetime'
import { getErrorMessage } from '@/utils/error'

// 当前路由，用在 workspaceId 与可选 conversationId query
const route = useRoute()
// 路由实例，用在返回详情
const router = useRouter()

// 当前空间 id，用在会话与来源 API
const workspaceId = computed(() => String(route.params.workspaceId || ''))
// 空间信息，用在页头
const workspace = ref<Workspace | null>(null)
// 会话列表，用在侧栏
const conversations = ref<Conversation[]>([])
// 当前选中会话 id
const activeConversationId = ref<string | null>(null)
// 当前会话详情含消息
const detail = ref<ConversationDetail | null>(null)
// 侧栏加载中
const listLoading = ref(false)
// 详情加载中
const detailLoading = ref(false)
// 提问发送中
const asking = ref(false)
// 新建会话提交中
const creatingConversation = ref(false)
// 输入框问题
const question = ref('')
// 新建会话标题（可选）
const newConversationTitle = ref('')
// 模型档列表，用在可选覆盖
const modelProfiles = ref<ModelProfile[]>([])
// 选中聊天模型档；空则默认
const selectedChatProfileId = ref<string>('')
// 选中嵌入模型档；空则默认
const selectedEmbeddingProfileId = ref<string>('')
// 空间内 ready 来源数，用在提示
const readySourceCount = ref(0)
// 消息列表滚动容器，用在发送后滚底
const messageScrollRef = ref<HTMLElement | null>(null)

// 聊天模型档选项，用在下拉
const chatProfiles = computed(() =>
  modelProfiles.value.filter((item) => item.purpose === ModelPurposeValue.Chat),
)
// 嵌入模型档选项，用在下拉
const embeddingProfiles = computed(() =>
  modelProfiles.value.filter((item) => item.purpose === ModelPurposeValue.Embedding),
)

// 加载空间、会话、模型档与 ready 来源数，用在挂载
async function loadPage(): Promise<void> {
  if (!workspaceId.value) {
    return
  }
  listLoading.value = true
  try {
    const [workspaceInfo, conversationList, profiles, sources] = await Promise.all([
      getWorkspace(workspaceId.value),
      listConversations(workspaceId.value),
      listModelProfiles(),
      listSources(workspaceId.value),
    ])
    workspace.value = workspaceInfo
    conversations.value = conversationList
    modelProfiles.value = profiles
    readySourceCount.value = sources.filter((item) => item.status === SourceStatusValue.Ready).length

    if (conversationList.length > 0 && !activeConversationId.value) {
      await selectConversation(conversationList[0].id)
    } else if (conversationList.length === 0) {
      detail.value = null
      activeConversationId.value = null
    }
  } catch (error) {
    ElMessage.error(getErrorMessage(error, '加载会话失败'))
    void router.push({ name: 'workspace-detail', params: { workspaceId: workspaceId.value } })
  } finally {
    listLoading.value = false
  }
}

// 切换会话并拉取消息，用在侧栏点击
async function selectConversation(conversationId: string): Promise<void> {
  activeConversationId.value = conversationId
  detailLoading.value = true
  try {
    detail.value = await getConversation(conversationId)
    await scrollToBottom()
  } catch (error) {
    ElMessage.error(getErrorMessage(error, '加载会话消息失败'))
  } finally {
    detailLoading.value = false
  }
}

// 新建会话并选中，用在「新建会话」按钮
async function handleCreateConversation(): Promise<void> {
  creatingConversation.value = true
  try {
    const created = await createConversation(workspaceId.value, {
      title: newConversationTitle.value.trim() || null,
    })
    conversations.value = [created, ...conversations.value]
    newConversationTitle.value = ''
    await selectConversation(created.id)
  } catch (error) {
    ElMessage.error(getErrorMessage(error, '创建会话失败'))
  } finally {
    creatingConversation.value = false
  }
}

// 确认删除会话，用在侧栏删除按钮
async function handleDeleteConversation(conversation: Conversation): Promise<void> {
  try {
    await ElMessageBox.confirm(
      `确认删除会话「${conversation.title || '未命名会话'}」？不会删除空间下来源。`,
      '删除会话',
      {
        type: 'warning',
        confirmButtonText: '删除',
        cancelButtonText: '取消',
      },
    )
  } catch {
    return
  }

  try {
    await deleteConversation(conversation.id)
    conversations.value = conversations.value.filter((item) => item.id !== conversation.id)
    if (activeConversationId.value === conversation.id) {
      activeConversationId.value = null
      detail.value = null
      if (conversations.value.length > 0) {
        await selectConversation(conversations.value[0].id)
      }
    }
    ElMessage.success('会话已删除')
  } catch (error) {
    ElMessage.error(getErrorMessage(error, '删除会话失败'))
  }
}

// 发送严格边界提问，用在输入框发送
async function handleAsk(): Promise<void> {
  if (!activeConversationId.value) {
    ElMessage.warning('请先创建并选中一个会话')
    return
  }
  // 去空白问题，用在请求与前端拦截
  const content = question.value.trim()
  if (!content) {
    ElMessage.warning('请输入问题')
    return
  }

  // 提问载荷，用在 askMessage
  const payload: AskMessageRequest = {
    content,
    chatModelProfileId: selectedChatProfileId.value || null,
    embeddingModelProfileId: selectedEmbeddingProfileId.value || null,
  }

  asking.value = true
  try {
    const response = await askMessage(activeConversationId.value, payload)
    question.value = ''
    if (detail.value) {
      detail.value.messages = [
        ...detail.value.messages,
        response.userMessage,
        response.assistantMessage,
      ]
      if (!detail.value.title) {
        detail.value.title = response.userMessage.content.slice(0, 30)
      }
    }
    // 同步侧栏标题与更新时间
    const conversation = conversations.value.find((item) => item.id === activeConversationId.value)
    if (conversation && !conversation.title) {
      conversation.title = response.userMessage.content.slice(0, 30)
    }
    await scrollToBottom()
  } catch (error) {
    ElMessage.error(getErrorMessage(error, '提问失败'))
  } finally {
    asking.value = false
  }
}

// 把消息区滚到底部，用在加载与发送后
async function scrollToBottom(): Promise<void> {
  await nextTick()
  if (messageScrollRef.value) {
    messageScrollRef.value.scrollTop = messageScrollRef.value.scrollHeight
  }
}

// 判断助手消息，用在气泡左右布局
function isAssistant(message: Message): boolean {
  return message.role === 'assistant'
}

// 返回空间详情，用在页头返回
function goBack(): void {
  void router.push({ name: 'workspace-detail', params: { workspaceId: workspaceId.value } })
}

watch(workspaceId, () => {
  activeConversationId.value = null
  detail.value = null
  void loadPage()
})

onMounted(() => {
  void loadPage()
})
</script>

<template>
  <div class="flex flex-col gap-[16px]">
    <div class="flex items-start justify-between gap-[16px]">
      <div class="min-w-0 flex-1">
        <el-button :icon="ArrowLeft" text class="mb-[8px] px-0" @click="goBack">
          返回空间详情
        </el-button>
        <div class="text-2xl text-[#111827]">{{ workspace?.name || '会话问答' }}</div>
        <div class="mt-[8px] text-sm text-[#6B7280]">
          回答模式：{{ ANSWER_MODE_STRICT }} · 可检索来源 {{ readySourceCount }} 条
        </div>
      </div>
    </div>

    <div class="grid min-h-[560px] grid-cols-1 gap-[16px] xl:grid-cols-[280px_minmax(0,1fr)]">
      <div class="rounded-[12px] bg-white p-[16px] shadow-sm">
        <div class="mb-[12px] text-lg text-[#111827]">会话</div>
        <el-input
          v-model="newConversationTitle"
          class="mb-[12px]"
          placeholder="可选：新会话标题"
          maxlength="100"
        />
        <el-button
          type="primary"
          class="mb-[16px] w-full"
          :icon="Plus"
          :loading="creatingConversation"
          @click="handleCreateConversation"
        >
          新建会话
        </el-button>

        <div v-loading="listLoading" class="flex max-h-[420px] flex-col gap-[8px] overflow-y-auto scrollbar-hide">
          <div
            v-for="conversation in conversations"
            :key="conversation.id"
            class="cursor-pointer rounded-[8px] border p-[12px] transition-colors"
            :class="
              activeConversationId === conversation.id
                ? 'border-[#2563EB] bg-[#EEF2FF]'
                : 'border-[#E5E7EB] hover:bg-[#F9FAFB]'
            "
            @click="selectConversation(conversation.id)"
          >
            <div class="flex items-start justify-between gap-[8px]">
              <div class="min-w-0 flex-1">
                <div class="truncate text-sm text-[#111827]">
                  {{ conversation.title || '未命名会话' }}
                </div>
                <div class="mt-[4px] text-xs text-[#9CA3AF]">
                  {{ formatDateTime(conversation.updatedAt) }}
                </div>
              </div>
              <el-button
                link
                type="danger"
                :icon="Delete"
                @click.stop="handleDeleteConversation(conversation)"
              />
            </div>
          </div>
          <div v-if="conversations.length === 0 && !listLoading" class="text-sm text-[#9CA3AF]">
            暂无会话，先新建一个
          </div>
        </div>
      </div>

      <div class="flex min-h-[560px] flex-col rounded-[12px] bg-white p-[16px] shadow-sm">
        <div v-loading="detailLoading" class="flex min-h-0 flex-1 flex-col">
          <div v-if="!activeConversationId" class="flex flex-1 items-center justify-center text-sm text-[#9CA3AF]">
            请先新建或选择一个会话
          </div>

          <template v-else>
            <div ref="messageScrollRef" class="flex min-h-[280px] flex-1 flex-col gap-[16px] overflow-y-auto pr-[8px] scrollbar-hide">
              <div
                v-for="message in detail?.messages || []"
                :key="message.id"
                class="flex"
                :class="isAssistant(message) ? 'justify-start' : 'justify-end'"
              >
                <div
                  class="max-w-[85%] rounded-[12px] px-[16px] py-[12px] text-sm"
                  :class="
                    isAssistant(message)
                      ? 'bg-[#F3F4F6] text-[#111827]'
                      : 'bg-[#2563EB] text-white'
                  "
                >
                  <div class="whitespace-pre-wrap">{{ message.content }}</div>

                  <div
                    v-if="isAssistant(message) && message.citations.length > 0"
                    class="mt-[12px] flex flex-col gap-[8px] border-t border-[#D1D5DB] pt-[12px]"
                  >
                    <div class="text-xs text-[#6B7280]">引用</div>
                    <div
                      v-for="citation in message.citations"
                      :key="`${citation.sourceId}-${citation.chunkId}`"
                      class="rounded-[8px] bg-white p-[8px] text-xs text-[#374151]"
                    >
                      <div class="font-medium text-[#111827]">{{ citation.title }}</div>
                      <div v-if="citation.snippet" class="mt-[4px] text-[#6B7280]">
                        {{ citation.snippet }}
                      </div>
                    </div>
                  </div>

                  <div
                    class="mt-[8px] text-xs"
                    :class="isAssistant(message) ? 'text-[#9CA3AF]' : 'text-[#BFDBFE]'"
                  >
                    {{ formatDateTime(message.createdAt) }}
                  </div>
                </div>
              </div>

              <div v-if="(detail?.messages.length || 0) === 0" class="text-sm text-[#9CA3AF]">
                向当前知识空间提问；无可靠依据时会固定拒答。
              </div>
              <div v-if="asking" class="text-sm text-[#6B7280]">正在检索并生成…</div>
            </div>

            <div class="mt-[16px] border-t border-[#E5E7EB] pt-[16px]">
              <div class="mb-[12px] grid grid-cols-1 gap-[12px] md:grid-cols-2">
                <div>
                  <div class="mb-[6px] text-xs text-[#6B7280]">聊天模型（可选，默认系统档）</div>
                  <el-select
                    v-model="selectedChatProfileId"
                    clearable
                    placeholder="系统默认"
                    class="w-full"
                  >
                    <el-option
                      v-for="profile in chatProfiles"
                      :key="profile.id"
                      :label="profile.isSystemDefault ? `${profile.name}（默认）` : profile.name"
                      :value="profile.id"
                    />
                  </el-select>
                </div>
                <div>
                  <div class="mb-[6px] text-xs text-[#6B7280]">嵌入模型（可选，默认系统档）</div>
                  <el-select
                    v-model="selectedEmbeddingProfileId"
                    clearable
                    placeholder="系统默认"
                    class="w-full"
                  >
                    <el-option
                      v-for="profile in embeddingProfiles"
                      :key="profile.id"
                      :label="profile.isSystemDefault ? `${profile.name}（默认）` : profile.name"
                      :value="profile.id"
                    />
                  </el-select>
                </div>
              </div>

              <el-input
                v-model="question"
                type="textarea"
                :rows="3"
                placeholder="输入问题，Enter 发送（Shift+Enter 换行）"
                :disabled="asking"
                @keydown.enter.exact.prevent="handleAsk"
              />
              <div class="mt-[12px] flex justify-end">
                <el-button
                  type="primary"
                  :icon="Promotion"
                  :loading="asking"
                  :disabled="!activeConversationId"
                  @click="handleAsk"
                >
                  发送
                </el-button>
              </div>
            </div>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>
