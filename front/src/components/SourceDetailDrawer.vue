<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'

import type { PlainTextSourceUpdate, Source } from '@knowledgescope/shared'
import { MVP_SOURCE_STATUS, MVP_SOURCE_TYPE } from '@knowledgescope/shared'

import { deleteSource, getSource, updateSource } from '@/api/sources'
import {
  SOURCE_CONTENT_MAX_LENGTH,
  SOURCE_TITLE_MAX_LENGTH,
} from '@/constants/ui'
import { formatDateTime } from '@/utils/datetime'
import { getErrorMessage } from '@/utils/error'

const props = defineProps<{
  modelValue: boolean
  workspaceId: string
  sourceId: string | null
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  changed: []
}>()

// 抽屉显隐双向绑定，用在 el-drawer
const visible = computed({
  get: () => props.modelValue,
  set: (value: boolean) => emit('update:modelValue', value),
})

// 详情加载中，用在抽屉骨架态
const loading = ref(false)
// 保存中，用在编辑保存按钮
const saving = ref(false)
// 是否处于编辑模式，用在切换只读/表单
const editing = ref(false)
// 当前来源详情，用在展示与编辑回填
const detail = ref<Source | null>(null)
// 编辑表单引用，用在校验
const formRef = ref<FormInstance>()
// 编辑表单字段，用在 PATCH 请求
const form = reactive({
  title: '',
  content: '',
})

// 编辑校验规则，用在 el-form
const rules: FormRules = {
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
    { required: true, message: '请输入正文', trigger: 'blur' },
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

// 拉取来源详情并填入表单，用在打开抽屉时
async function loadDetail(): Promise<void> {
  if (!props.sourceId) {
    detail.value = null
    return
  }

  loading.value = true
  editing.value = false
  try {
    detail.value = await getSource(props.workspaceId, props.sourceId)
    form.title = detail.value.title
    form.content = detail.value.content ?? ''
  } catch (error) {
    ElMessage.error(getErrorMessage(error, '加载来源详情失败'))
    visible.value = false
  } finally {
    loading.value = false
  }
}

watch(
  () => [props.modelValue, props.sourceId, props.workspaceId] as const,
  ([open]) => {
    if (open) {
      void loadDetail()
    }
  },
)

// 进入编辑模式，用在「编辑」按钮
function startEdit(): void {
  if (!detail.value) {
    return
  }
  form.title = detail.value.title
  form.content = detail.value.content ?? ''
  editing.value = true
}

// 取消编辑并恢复原文，用在「取消」按钮
function cancelEdit(): void {
  if (!detail.value) {
    editing.value = false
    return
  }
  form.title = detail.value.title
  form.content = detail.value.content ?? ''
  editing.value = false
}

// 保存标题/正文修改，用在编辑态保存按钮
async function handleSave(): Promise<void> {
  if (!props.sourceId || !formRef.value) {
    return
  }
  // 校验结果，用在阻止无效提交
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) {
    return
  }

  // PATCH 载荷，用在 updateSource
  const payload: PlainTextSourceUpdate = {
    title: form.title.trim() || undefined,
    content: form.content.trim(),
  }

  saving.value = true
  try {
    detail.value = await updateSource(props.workspaceId, props.sourceId, payload)
    editing.value = false
    ElMessage.success('来源已更新')
    emit('changed')
  } catch (error) {
    ElMessage.error(getErrorMessage(error, '更新来源失败'))
  } finally {
    saving.value = false
  }
}

// 确认并删除当前来源，用在抽屉底部删除按钮
async function handleDelete(): Promise<void> {
  if (!props.sourceId || !detail.value) {
    return
  }

  try {
    await ElMessageBox.confirm(
      `确认删除来源「${detail.value.title}」？此操作不可恢复。`,
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
    await deleteSource(props.workspaceId, props.sourceId)
    ElMessage.success('来源已删除')
    visible.value = false
    emit('changed')
  } catch (error) {
    ElMessage.error(getErrorMessage(error, '删除来源失败'))
  }
}
</script>

<template>
  <el-drawer v-model="visible" title="来源详情" size="480px" destroy-on-close>
    <div v-loading="loading" class="min-h-[240px]">
      <template v-if="detail && !editing">
        <div class="flex flex-col gap-[16px]">
          <div>
            <div class="text-lg text-[#111827]">{{ detail.title }}</div>
            <div class="mt-[8px] flex flex-wrap gap-[8px]">
              <el-tag size="small">{{ detail.type || MVP_SOURCE_TYPE }}</el-tag>
              <el-tag size="small" type="success">{{ detail.status || MVP_SOURCE_STATUS }}</el-tag>
            </div>
          </div>
          <div class="text-sm text-[#6B7280]">
            <div>创建：{{ formatDateTime(detail.createdAt) }}</div>
            <div>更新：{{ formatDateTime(detail.updatedAt) }}</div>
          </div>
          <div class="whitespace-pre-wrap rounded-[8px] bg-[#F9FAFB] p-[16px] text-sm text-[#374151]">
            {{ detail.content }}
          </div>
          <div class="flex justify-end gap-[8px]">
            <el-button type="danger" plain @click="handleDelete">删除</el-button>
            <el-button type="primary" @click="startEdit">编辑</el-button>
          </div>
        </div>
      </template>

      <template v-else-if="detail && editing">
        <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
          <el-form-item label="标题" prop="title">
            <el-input
              v-model="form.title"
              :maxlength="SOURCE_TITLE_MAX_LENGTH"
              show-word-limit
              placeholder="可选；留空则保持或由服务端规则处理"
            />
          </el-form-item>
          <el-form-item label="正文" prop="content">
            <el-input
              v-model="form.content"
              type="textarea"
              :rows="12"
              :maxlength="SOURCE_CONTENT_MAX_LENGTH"
              show-word-limit
              placeholder="纯文字正文"
            />
          </el-form-item>
        </el-form>
        <div class="flex justify-end gap-[8px]">
          <el-button @click="cancelEdit">取消</el-button>
          <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
        </div>
      </template>
    </div>
  </el-drawer>
</template>
