<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  ElMessage,
  ElMessageBox,
  type FormInstance,
  type FormRules,
} from 'element-plus'
import { ArrowLeft, Delete, EditPen } from '@element-plus/icons-vue'

import type {
  PlainTextSourceCreate,
  SourceListItem,
  Workspace,
  WorkspaceCreate,
  WorkspaceUpdate,
} from '@knowledgescope/shared'
import { MVP_SOURCE_STATUS, MVP_SOURCE_TYPE } from '@knowledgescope/shared'

import { createSource, deleteSource, listSources } from '@/api/sources'
import {
  deleteWorkspace,
  getWorkspace,
  updateWorkspace,
} from '@/api/workspaces'
import SourceDetailDrawer from '@/components/SourceDetailDrawer.vue'
import WorkspaceFormDialog from '@/components/WorkspaceFormDialog.vue'
import {
  SOURCE_CONTENT_MAX_LENGTH,
  SOURCE_TITLE_MAX_LENGTH,
} from '@/constants/ui'
import { formatDateTime } from '@/utils/datetime'
import { getErrorMessage } from '@/utils/error'

// 当前路由，用在读取 workspaceId
const route = useRoute()
// 路由实例，用在返回列表与删除后跳转
const router = useRouter()

// 路由中的空间 id，用在全部 API 调用
const workspaceId = computed(() => String(route.params.workspaceId || ''))

// 空间详情，用在页头展示与编辑回填
const workspace = ref<Workspace | null>(null)
// 来源列表，用在表格
const sources = ref<SourceListItem[]>([])
// 页头加载中，用在整体 loading
const loading = ref(false)
// 投递提交中，用在投递按钮
const creatingSource = ref(false)
// 空间编辑对话框显隐
const editDialogVisible = ref(false)
// 空间编辑提交中
const editSubmitting = ref(false)
// 来源详情抽屉显隐
const drawerVisible = ref(false)
// 当前查看的来源 id，用在抽屉
const activeSourceId = ref<string | null>(null)

// 投递表单引用，用在校验
const sourceFormRef = ref<FormInstance>()
// 投递表单字段，用在 createSource
const sourceForm = reactive({
  title: '',
  content: '',
})

// 投递表单校验，用在 el-form
const sourceRules: FormRules = {
  title: [
    {
      validator: (_rule, value: string, callback) => {
        if (value && value.trim().length > SOURCE_TITLE_MAX_LENGTH) {
          callback(new Error(`标题最长 ${SOURCE_TITLE_MAX_LENGTH} 字`))
          return
        }
        callback()
      },
      trigger: 'blur',
    },
  ],
  content: [
    { required: true, message: '请粘贴或输入纯文字正文', trigger: 'blur' },
    {
      validator: (_rule, value: string, callback) => {
        if (!value || !value.trim()) {
          callback(new Error('正文去首尾空白后不能为空'))
          return
        }
        if (value.length > SOURCE_CONTENT_MAX_LENGTH) {
          callback(new Error(`正文最长 ${SOURCE_CONTENT_MAX_LENGTH} 字`))
          return
        }
        callback()
      },
      trigger: 'blur',
    },
  ],
}

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

// 仅刷新来源列表与空间计数，用在投递/删除后来源变更
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

// 返回空间列表，用在页头返回按钮
function goBack(): void {
  void router.push({ name: 'workspace-list' })
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
      `确认删除知识空间「${workspace.value.name}」？其下全部来源将一并删除。`,
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

// 投递纯文字来源，用在投递表单提交
async function handleCreateSource(): Promise<void> {
  if (!workspaceId.value || !sourceFormRef.value) {
    return
  }
  // 表单校验结果，用在阻止空正文
  const valid = await sourceFormRef.value.validate().catch(() => false)
  if (!valid) {
    return
  }

  // 创建载荷；标题空则不传，交给后端生成
  const payload: PlainTextSourceCreate = {
    title: sourceForm.title.trim() || null,
    content: sourceForm.content.trim(),
  }

  creatingSource.value = true
  try {
    await createSource(workspaceId.value, payload)
    ElMessage.success('已投递纯文字来源')
    sourceForm.title = ''
    sourceForm.content = ''
    sourceFormRef.value.resetFields()
    await refreshSources()
  } catch (error) {
    ElMessage.error(getErrorMessage(error, '投递来源失败'))
  } finally {
    creatingSource.value = false
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
      `确认删除来源「${source.title}」？此操作不可恢复。`,
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
        <el-button :icon="EditPen" @click="openEditDialog">编辑</el-button>
        <el-button type="danger" plain :icon="Delete" @click="handleDeleteWorkspace">
          删除空间
        </el-button>
      </div>
    </div>

    <div class="grid grid-cols-1 gap-[16px] xl:grid-cols-[360px_minmax(0,1fr)]">
      <div class="rounded-[12px] bg-white p-[16px] shadow-sm">
        <div class="mb-[12px] text-lg text-[#111827]">投递纯文字</div>
        <div class="mb-[12px] text-sm text-[#6B7280]">
          MVP 仅支持 {{ MVP_SOURCE_TYPE }}，创建后状态为 {{ MVP_SOURCE_STATUS }}
        </div>
        <el-form
          ref="sourceFormRef"
          :model="sourceForm"
          :rules="sourceRules"
          label-position="top"
        >
          <el-form-item label="标题（可选）" prop="title">
            <el-input
              v-model="sourceForm.title"
              :maxlength="SOURCE_TITLE_MAX_LENGTH"
              show-word-limit
              placeholder="不填则由服务端用正文前缀生成"
            />
          </el-form-item>
          <el-form-item label="正文" prop="content">
            <el-input
              v-model="sourceForm.content"
              type="textarea"
              :rows="10"
              :maxlength="SOURCE_CONTENT_MAX_LENGTH"
              show-word-limit
              placeholder="粘贴一段纯文字资料…"
            />
          </el-form-item>
          <el-button
            type="primary"
            class="w-full"
            :loading="creatingSource"
            @click="handleCreateSource"
          >
            保存为来源
          </el-button>
        </el-form>
      </div>

      <div class="rounded-[12px] bg-white p-[16px] shadow-sm">
        <div class="mb-[12px] flex items-center justify-between">
          <div class="text-lg text-[#111827]">来源列表</div>
          <div class="text-sm text-[#6B7280]">共 {{ sources.length }} 条</div>
        </div>
        <el-table
          :data="sources"
          empty-text="暂无来源，先在左侧投递一段纯文字"
          class="w-full"
          @row-click="openSourceDrawer"
        >
          <el-table-column prop="title" label="标题" min-width="160" />
          <el-table-column label="预览" min-width="220">
            <template #default="{ row }">
              <div class="truncate text-[#4B5563]">{{ row.contentPreview }}</div>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-tag size="small" type="success">{{ row.status }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="创建时间" width="180">
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
