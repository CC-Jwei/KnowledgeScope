<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, ChatDotRound, Delete, EditPen } from '@element-plus/icons-vue'

import type { SourceListItem, Workspace, WorkspaceCreate, WorkspaceUpdate } from '@knowledgescope/shared'

import { deleteSource, listSources } from '@/api/sources'
import { deleteWorkspace, getWorkspace, updateWorkspace } from '@/api/workspaces'
import SourceCreateForm from '@/components/SourceCreateForm.vue'
import SourceDetailDrawer from '@/components/SourceDetailDrawer.vue'
import WorkspaceFormDialog from '@/components/WorkspaceFormDialog.vue'
import { formatDateTime } from '@/utils/datetime'
import { getErrorMessage } from '@/utils/error'
import { isSourceInProgress, SOURCE_STATUS_LABEL, SOURCE_TYPE_LABEL, sourceStatusTagType } from '@/utils/sourceStatus'

// 当前路由，用在读取 workspaceId
const route = useRoute()
// 路由实例，用在返回列表与跳转会话
const router = useRouter()

// 路由中的空间 id，用在全部 API 调用
const workspaceId = computed(() => String(route.params.workspaceId || ''))

// 空间详情，用在页头展示与编辑回填
const workspace = ref<Workspace | null>(null)
// 来源列表，用在表格
const sources = ref<SourceListItem[]>([])
// 页头加载中，用在整体 loading
const loading = ref(false)
// 空间编辑对话框显隐
const editDialogVisible = ref(false)
// 空间编辑提交中
const editSubmitting = ref(false)
// 来源详情抽屉显隐
const drawerVisible = ref(false)
// 当前查看的来源 id，用在抽屉
const activeSourceId = ref<string | null>(null)
// 状态轮询定时器，用在 pending/processing 列表
let pollTimer: ReturnType<typeof setTimeout> | null = null

// 是否存在入库中来源，用在与轮询开关
const hasInProgressSources = computed(() =>
  sources.value.some((item) => isSourceInProgress(item.status)),
)

// 并行加载空间详情与来源列表，用在挂载与刷新
async function loadPage(): Promise<void> {
  if (!workspaceId.value) {
    return
  }

  loading.value = true
  try {
    // 详情与列表并行结果，用在填充页面状态
    const [workspaceDetail, sourceList] = await Promise.all([
      getWorkspace(workspaceId.value),
      listSources(workspaceId.value),
    ])
    workspace.value = workspaceDetail
    sources.value = sourceList
  } catch (error) {
    ElMessage.error(getErrorMessage(error, '加载空间详情失败'))
    void router.push({ name: 'workspace-list' })
  } finally {
    loading.value = false
  }
}

// 刷新来源列表与空间计数，用在投递/删除/轮询
async function refreshSources(): Promise<void> {
  if (!workspaceId.value) {
    return
  }
  try {
    sources.value = await listSources(workspaceId.value)
    workspace.value = await getWorkspace(workspaceId.value)
  } catch (error) {
    ElMessage.error(getErrorMessage(error, '刷新来源列表失败'))
  }
}

// 清理轮询定时器，用在卸载与无在途来源
function clearPollTimer(): void {
  if (pollTimer) {
    clearTimeout(pollTimer)
    pollTimer = null
  }
}

// 若仍有 pending/processing 则 2 秒后再拉一次，用在入库状态轮询
function schedulePoll(): void {
  clearPollTimer()
  if (!hasInProgressSources.value) {
    return
  }
  pollTimer = setTimeout(() => {
    void refreshSources()
  }, 2000)
}

watch(hasInProgressSources, () => {
  schedulePoll()
})

// 返回空间列表，用在页头返回按钮
function goBack(): void {
  void router.push({ name: 'workspace-list' })
}

// 进入会话问答页，用在页头入口
function goChat(): void {
  void router.push({
    name: 'workspace-chat',
    params: { workspaceId: workspaceId.value },
  })
}

// 打开空间编辑对话框，用在「编辑」按钮
function openEditDialog(): void {
  editDialogVisible.value = true
}

// 提交空间编辑，用在 WorkspaceFormDialog
async function handleEditSubmit(payload: WorkspaceCreate | WorkspaceUpdate): Promise<void> {
  if (!workspaceId.value) {
    return
  }
  editSubmitting.value = true
  try {
    workspace.value = await updateWorkspace(workspaceId.value, payload as WorkspaceUpdate)
    editDialogVisible.value = false
    ElMessage.success('空间信息已更新')
  } catch (error) {
    ElMessage.error(getErrorMessage(error, '更新空间失败'))
  } finally {
    editSubmitting.value = false
  }
}

// 确认删除整个空间，用在页头删除按钮
async function handleDeleteWorkspace(): Promise<void> {
  if (!workspace.value) {
    return
  }
  try {
    await ElMessageBox.confirm(
      `确认删除知识空间「${workspace.value.name}」？来源、会话、分块与向量将一并删除。`,
      '删除知识空间',
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
    await deleteWorkspace(workspace.value.id)
    ElMessage.success('知识空间已删除')
    void router.push({ name: 'workspace-list' })
  } catch (error) {
    ElMessage.error(getErrorMessage(error, '删除知识空间失败'))
  }
}

// 打开来源详情抽屉，用在表格行/查看按钮
function openSourceDrawer(source: SourceListItem): void {
  activeSourceId.value = source.id
  drawerVisible.value = true
}

// 确认删除列表中的来源，用在表格删除按钮
async function handleDeleteSource(source: SourceListItem): Promise<void> {
  try {
    await ElMessageBox.confirm(
      `确认删除来源「${source.title}」？其分块与向量将一并清理。`,
      '删除来源',
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
    await deleteSource(workspaceId.value, source.id)
    ElMessage.success('来源已删除')
    if (activeSourceId.value === source.id) {
      drawerVisible.value = false
      activeSourceId.value = null
    }
    await refreshSources()
  } catch (error) {
    ElMessage.error(getErrorMessage(error, '删除来源失败'))
  }
}

watch(workspaceId, () => {
  void loadPage()
})

onMounted(() => {
  void loadPage()
})

onUnmounted(() => {
  clearPollTimer()
})
</script>

<template>
  <div v-loading="loading" class="flex flex-col gap-[16px]">
    <div class="flex items-start justify-between gap-[16px]">
      <div class="min-w-0 flex-1">
        <el-button :icon="ArrowLeft" text class="mb-[8px] px-0" @click="goBack">
          返回空间列表
        </el-button>
        <div class="text-2xl text-[#111827]">{{ workspace?.name || '空间详情' }}</div>
        <div class="mt-[8px] text-sm text-[#6B7280]">
          {{ workspace?.description || '暂无描述' }}
        </div>
        <div class="mt-[8px] flex flex-wrap gap-[16px] text-sm text-[#6B7280]">
          <div>来源 {{ workspace?.sourceCount ?? 0 }}</div>
          <div>创建 {{ formatDateTime(workspace?.createdAt) }}</div>
          <div>更新 {{ formatDateTime(workspace?.updatedAt) }}</div>
        </div>
      </div>
      <div class="flex shrink-0 gap-[8px]">
        <el-button type="primary" plain :icon="ChatDotRound" @click="goChat">会话问答</el-button>
        <el-button :icon="EditPen" @click="openEditDialog">编辑</el-button>
        <el-button type="danger" plain :icon="Delete" @click="handleDeleteWorkspace">
          删除空间
        </el-button>
      </div>
    </div>

    <div class="grid grid-cols-1 gap-[16px] xl:grid-cols-[360px_minmax(0,1fr)]">
      <SourceCreateForm :workspace-id="workspaceId" @created="refreshSources" />

      <div class="rounded-[12px] bg-white p-[16px] shadow-sm">
        <div class="mb-[12px] flex items-center justify-between">
          <div class="text-lg text-[#111827]">来源列表</div>
          <div class="flex items-center gap-[12px] text-sm text-[#6B7280]">
            <div v-if="hasInProgressSources">正在刷新入库状态…</div>
            <div>共 {{ sources.length }} 条</div>
          </div>
        </div>
        <el-table
          :data="sources"
          empty-text="暂无来源，先在左侧投递"
          class="w-full"
          @row-click="openSourceDrawer"
        >
          <el-table-column prop="title" label="标题" min-width="140" />
          <el-table-column label="类型" width="110">
            <template #default="{ row }">
              <el-tag size="small" effect="plain">{{ SOURCE_TYPE_LABEL[row.type] || row.type }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="预览" min-width="180">
            <template #default="{ row }">
              <div class="truncate text-[#4B5563]">{{ row.contentPreview || '—' }}</div>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="120">
            <template #default="{ row }">
              <el-tag size="small" :type="sourceStatusTagType(row.status)">
                {{ SOURCE_STATUS_LABEL[row.status] }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="创建时间" width="170">
            <template #default="{ row }">
              {{ formatDateTime(row.createdAt) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="160" fixed="right">
            <template #default="{ row }">
              <div class="flex items-center gap-[8px]" @click.stop>
                <el-button link type="primary" @click="openSourceDrawer(row)">查看</el-button>
                <el-button link type="danger" @click="handleDeleteSource(row)">删除</el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>

    <WorkspaceFormDialog
      v-model="editDialogVisible"
      mode="edit"
      :initial="workspace"
      :submitting="editSubmitting"
      @submit="handleEditSubmit"
    />

    <SourceDetailDrawer
      v-model="drawerVisible"
      :workspace-id="workspaceId"
      :source-id="activeSourceId"
      @changed="refreshSources"
    />
  </div>
</template>
