<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Delete, Plus } from '@element-plus/icons-vue'

import type { Workspace, WorkspaceCreate, WorkspaceUpdate } from '@knowledgescope/shared'

import {
  createWorkspace,
  deleteWorkspace,
  listWorkspaces,
} from '@/api/workspaces'
import WorkspaceFormDialog from '@/components/WorkspaceFormDialog.vue'
import { formatDateTime } from '@/utils/datetime'
import { getErrorMessage } from '@/utils/error'

// 路由实例，用在进入空间详情
const router = useRouter()
// 空间列表数据，用在表格渲染
const workspaces = ref<Workspace[]>([])
// 列表加载中，用在表格 loading
const loading = ref(false)
// 新建对话框显隐，用在 WorkspaceFormDialog
const dialogVisible = ref(false)
// 新建提交中，用在对话框保存按钮
const submitting = ref(false)

// 拉取全部知识空间，用在挂载与增删后刷新
async function fetchWorkspaces(): Promise<void> {
  loading.value = true
  try {
    workspaces.value = await listWorkspaces()
  } catch (error) {
    ElMessage.error(getErrorMessage(error, '加载知识空间失败'))
  } finally {
    loading.value = false
  }
}

// 打开新建对话框，用在「创建知识空间」按钮
function openCreateDialog(): void {
  dialogVisible.value = true
}

// 提交新建空间，用在对话框 submit
async function handleCreate(payload: WorkspaceCreate | WorkspaceUpdate): Promise<void> {
  submitting.value = true
  try {
    // 创建接口只要 WorkspaceCreate 字段
    const created = await createWorkspace(payload as WorkspaceCreate)
    ElMessage.success(`已创建「${created.name}」`)
    dialogVisible.value = false
    await fetchWorkspaces()
  } catch (error) {
    ElMessage.error(getErrorMessage(error, '创建知识空间失败'))
  } finally {
    submitting.value = false
  }
}

// 进入空间详情页，用在表格行点击与「打开」按钮
function openWorkspace(workspace: Workspace): void {
  void router.push({
    name: 'workspace-detail',
    params: { workspaceId: workspace.id },
  })
}

// 确认并删除空间，用在表格删除按钮
async function handleDelete(workspace: Workspace): Promise<void> {
  try {
    await ElMessageBox.confirm(
      `确认删除知识空间「${workspace.name}」？来源、会话、分块与向量将一并删除，且不可恢复。`,
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
    await deleteWorkspace(workspace.id)
    ElMessage.success('知识空间已删除')
    await fetchWorkspaces()
  } catch (error) {
    ElMessage.error(getErrorMessage(error, '删除知识空间失败'))
  }
}

onMounted(() => {
  void fetchWorkspaces()
})
</script>

<template>
  <div class="flex flex-col gap-[16px]">
    <div class="flex items-center justify-between gap-[16px]">
      <div>
        <div class="text-2xl text-[#111827]">知识空间</div>
        <div class="mt-[4px] text-sm text-[#6B7280]">
          仅展示当前登录用户的空间；详情页可投递来源并进入严格问答
        </div>
      </div>
      <el-button type="primary" :icon="Plus" @click="openCreateDialog">创建知识空间</el-button>
    </div>

    <div class="rounded-[12px] bg-white p-[16px] shadow-sm">
      <el-table
        v-loading="loading"
        :data="workspaces"
        empty-text="暂无知识空间，先创建一个"
        class="w-full"
        @row-click="openWorkspace"
      >
        <el-table-column prop="name" label="名称" min-width="180">
          <template #default="{ row }">
            <div class="cursor-pointer font-medium text-[#111827] transition-colors hover:text-[#2563EB]">
              {{ row.name }}
            </div>
          </template>
        </el-table-column>
        <el-table-column label="描述" min-width="240">
          <template #default="{ row }">
            <div class="truncate text-[#4B5563]">
              {{ row.description || '—' }}
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="sourceCount" label="来源数" width="100" />
        <el-table-column label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.createdAt) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <div class="flex items-center gap-[8px]" @click.stop>
              <el-button link type="primary" @click="openWorkspace(row)">打开</el-button>
              <el-button link type="danger" :icon="Delete" @click="handleDelete(row)">
                删除
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <WorkspaceFormDialog
      v-model="dialogVisible"
      mode="create"
      :submitting="submitting"
      @submit="handleCreate"
    />
  </div>
</template>
