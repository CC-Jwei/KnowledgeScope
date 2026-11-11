<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Delete, Plus } from '@element-plus/icons-vue'

import type { ModelProfile, ModelProfileCreate, ModelProfileUpdate } from '@knowledgescope/shared'
import { ModelPurposeValue, type ModelPurpose } from '@knowledgescope/shared'

import {
  createModelProfile,
  deleteModelProfile,
  listModelProfiles,
  updateModelProfile,
} from '@/api/modelProfiles'
import { formatDateTime } from '@/utils/datetime'
import { getErrorMessage } from '@/utils/error'

// 模型档列表，用在表格
const profiles = ref<ModelProfile[]>([])
// 列表加载中
const loading = ref(false)
// 对话框显隐
const dialogVisible = ref(false)
// 提交中
const submitting = ref(false)
// 当前编辑 id；空则新建
const editingId = ref<string | null>(null)
// 表单引用
const formRef = ref<FormInstance>()
// 表单字段，用在 create/update
const form = reactive({
  name: '',
  purpose: ModelPurposeValue.Chat as ModelPurpose,
  baseUrl: '',
  modelName: '',
  apiKey: '',
})

// 是否编辑模式，用在标题与 Key 必填
const isEditing = computed(() => Boolean(editingId.value))

// 表单校验，用在 el-form
const rules: FormRules = {
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  baseUrl: [{ required: true, message: '请输入 Base URL', trigger: 'blur' }],
  modelName: [{ required: true, message: '请输入模型名', trigger: 'blur' }],
  apiKey: [
    {
      validator: (_rule, value: string, callback) => {
        if (isEditing.value) {
          callback()
          return
        }
        if (!value || !value.trim()) {
          callback(new Error('新建时必须填写 API Key'))
          return
        }
        callback()
      },
      trigger: 'blur',
    },
  ],
}

// 拉取系统默认与个人档，用在挂载与增删改后
async function fetchProfiles(): Promise<void> {
  loading.value = true
  try {
    profiles.value = await listModelProfiles()
  } catch (error) {
    ElMessage.error(getErrorMessage(error, '加载模型档失败'))
  } finally {
    loading.value = false
  }
}

// 打开新建对话框，用在顶部按钮
function openCreateDialog(): void {
  editingId.value = null
  form.name = ''
  form.purpose = ModelPurposeValue.Chat
  form.baseUrl = ''
  form.modelName = ''
  form.apiKey = ''
  dialogVisible.value = true
}

// 打开编辑对话框（不允许系统默认），用在表格编辑
function openEditDialog(profile: ModelProfile): void {
  if (profile.isSystemDefault) {
    ElMessage.info('系统默认档由服务端环境变量维护，不可编辑')
    return
  }
  editingId.value = profile.id
  form.name = profile.name
  form.purpose = profile.purpose
  form.baseUrl = profile.baseUrl
  form.modelName = profile.modelName
  form.apiKey = ''
  dialogVisible.value = true
}

// 提交新建或更新，用在对话框保存
async function handleSubmit(): Promise<void> {
  if (!formRef.value) {
    return
  }
  // 校验结果，用在阻止无效请求
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) {
    return
  }

  submitting.value = true
  try {
    if (editingId.value) {
      // 更新载荷；Key 空则不传
      const payload: ModelProfileUpdate = {
        name: form.name.trim(),
        baseUrl: form.baseUrl.trim(),
        modelName: form.modelName.trim(),
      }
      if (form.apiKey.trim()) {
        payload.apiKey = form.apiKey.trim()
      }
      await updateModelProfile(editingId.value, payload)
      ElMessage.success('模型档已更新')
    } else {
      // 创建载荷
      const payload: ModelProfileCreate = {
        name: form.name.trim(),
        purpose: form.purpose,
        baseUrl: form.baseUrl.trim(),
        modelName: form.modelName.trim(),
        apiKey: form.apiKey.trim(),
      }
      await createModelProfile(payload)
      ElMessage.success('模型档已创建')
    }
    dialogVisible.value = false
    await fetchProfiles()
  } catch (error) {
    ElMessage.error(getErrorMessage(error, '保存模型档失败'))
  } finally {
    submitting.value = false
  }
}

// 确认删除个人档，用在表格删除
async function handleDelete(profile: ModelProfile): Promise<void> {
  if (profile.isSystemDefault) {
    ElMessage.info('不可删除系统默认档')
    return
  }
  try {
    await ElMessageBox.confirm(
      `确认删除模型档「${profile.name}」？`,
      '删除模型档',
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
    await deleteModelProfile(profile.id)
    ElMessage.success('模型档已删除')
    await fetchProfiles()
  } catch (error) {
    ElMessage.error(getErrorMessage(error, '删除模型档失败'))
  }
}

onMounted(() => {
  void fetchProfiles()
})
</script>

<template>
  <div class="flex flex-col gap-[16px]">
    <div class="flex items-center justify-between gap-[16px]">
      <div>
        <div class="text-2xl text-[#111827]">模型设置</div>
        <div class="mt-[4px] text-sm text-[#6B7280]">
          系统默认档来自服务端环境变量；个人档 Key 只写，列表仅展示脱敏
        </div>
      </div>
      <el-button type="primary" :icon="Plus" @click="openCreateDialog">新增模型档</el-button>
    </div>

    <div class="rounded-[12px] bg-white p-[16px] shadow-sm">
      <el-table v-loading="loading" :data="profiles" empty-text="暂无模型档">
        <el-table-column label="名称" min-width="180">
          <template #default="{ row }">
            <div class="flex items-center gap-[8px]">
              <div class="text-[#111827]">{{ row.name }}</div>
              <el-tag v-if="row.isSystemDefault" size="small" type="success">默认</el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="用途" width="100">
          <template #default="{ row }">
            {{ row.purpose === ModelPurposeValue.Chat ? '聊天' : '嵌入' }}
          </template>
        </el-table-column>
        <el-table-column prop="modelName" label="模型名" min-width="160" />
        <el-table-column label="Base URL" min-width="200">
          <template #default="{ row }">
            <div class="truncate text-[#4B5563]">{{ row.baseUrl || '—' }}</div>
          </template>
        </el-table-column>
        <el-table-column prop="apiKeyMasked" label="API Key" width="140" />
        <el-table-column label="更新时间" width="180">
          <template #default="{ row }">
            {{ row.updatedAt ? formatDateTime(row.updatedAt) : '—' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <div class="flex items-center gap-[8px]">
              <el-button link type="primary" :disabled="row.isSystemDefault" @click="openEditDialog(row)">
                编辑
              </el-button>
              <el-button
                link
                type="danger"
                :icon="Delete"
                :disabled="row.isSystemDefault"
                @click="handleDelete(row)"
              >
                删除
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-dialog
      v-model="dialogVisible"
      :title="isEditing ? '编辑模型档' : '新增模型档'"
      width="520px"
      destroy-on-close
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" maxlength="100" placeholder="例如：我的聊天模型" />
        </el-form-item>
        <el-form-item label="用途" prop="purpose">
          <el-select v-model="form.purpose" class="w-full" :disabled="isEditing">
            <el-option label="聊天" :value="ModelPurposeValue.Chat" />
            <el-option label="嵌入" :value="ModelPurposeValue.Embedding" />
          </el-select>
        </el-form-item>
        <el-form-item label="Base URL" prop="baseUrl">
          <el-input v-model="form.baseUrl" placeholder="https://…/v1" />
        </el-form-item>
        <el-form-item label="模型名" prop="modelName">
          <el-input v-model="form.modelName" placeholder="OpenAI 兼容模型名" />
        </el-form-item>
        <el-form-item
          :label="isEditing ? 'API Key（留空则保留原 Key）' : 'API Key'"
          prop="apiKey"
        >
          <el-input
            v-model="form.apiKey"
            type="password"
            show-password
            :placeholder="isEditing ? '不修改请留空' : '只写不完整回读'"
            autocomplete="new-password"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="flex justify-end gap-[8px]">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="submitting" @click="handleSubmit">保存</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>
