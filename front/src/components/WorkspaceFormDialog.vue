<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import type { FormInstance, FormRules } from 'element-plus'

import type { Workspace, WorkspaceCreate, WorkspaceUpdate } from '@knowledgescope/shared'

import {
  WORKSPACE_DESCRIPTION_MAX_LENGTH,
  WORKSPACE_NAME_MAX_LENGTH,
} from '@/constants/ui'

const props = defineProps<{
  modelValue: boolean
  mode: 'create' | 'edit'
  initial?: Pick<Workspace, 'name' | 'description'> | null
  submitting?: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  submit: [payload: WorkspaceCreate | WorkspaceUpdate]
}>()

// 对话框显隐双向绑定，用在 el-dialog
const visible = computed({
  get: () => props.modelValue,
  set: (value: boolean) => emit('update:modelValue', value),
})

// 表单引用，用在提交前校验
const formRef = ref<FormInstance>()

// 表单字段，用在创建/编辑提交
const form = reactive({
  name: '',
  description: '',
})

// 表单校验规则，用在 el-form
const rules: FormRules = {
  name: [
    { required: true, message: '请输入知识空间名称', trigger: 'blur' },
    {
      validator: (_rule, value: string, callback) => {
        if (!value || !value.trim()) {
          callback(new Error('名称去首尾空白后不能为空'))
          return
        }
        if (value.trim().length > WORKSPACE_NAME_MAX_LENGTH) {
          callback(new Error(`名称最长 ${WORKSPACE_NAME_MAX_LENGTH} 字`))
          return
        }
        callback()
      },
      trigger: 'blur',
    },
  ],
  description: [
    {
      validator: (_rule, value: string, callback) => {
        if (value && value.length > WORKSPACE_DESCRIPTION_MAX_LENGTH) {
          callback(new Error(`描述最长 ${WORKSPACE_DESCRIPTION_MAX_LENGTH} 字`))
          return
        }
        callback()
      },
      trigger: 'blur',
    },
  ],
}

// 对话框标题，用在 el-dialog title
const dialogTitle = computed(() => (props.mode === 'create' ? '创建知识空间' : '编辑知识空间'))

watch(
  () => props.modelValue,
  (open) => {
    if (!open) {
      return
    }
    form.name = props.initial?.name ?? ''
    form.description = props.initial?.description ?? ''
  },
)

// 校验并向上抛出提交载荷，用在确认按钮
async function handleSubmit(): Promise<void> {
  if (!formRef.value) {
    return
  }
  // 校验是否通过，用在决定是否 emit
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) {
    return
  }

  // 去空白后的名称，用在请求体
  const name = form.name.trim()
  // 去空白后的描述；空串转 null，用在请求体
  const description = form.description.trim() ? form.description.trim() : null

  if (props.mode === 'create') {
    // 创建载荷，用在父组件调用 createWorkspace
    const payload: WorkspaceCreate = { name, description }
    emit('submit', payload)
    return
  }

  // 编辑载荷，用在父组件调用 updateWorkspace
  const payload: WorkspaceUpdate = { name, description }
  emit('submit', payload)
}
</script>

<template>
  <el-dialog v-model="visible" :title="dialogTitle" width="520px" destroy-on-close>
    <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
      <el-form-item label="名称" prop="name">
        <el-input
          v-model="form.name"
          :maxlength="WORKSPACE_NAME_MAX_LENGTH"
          show-word-limit
          placeholder="例如：新能源汽车行业研究"
        />
      </el-form-item>
      <el-form-item label="描述" prop="description">
        <el-input
          v-model="form.description"
          type="textarea"
          :rows="3"
          :maxlength="WORKSPACE_DESCRIPTION_MAX_LENGTH"
          show-word-limit
          placeholder="可选，简要说明这个空间收录什么资料"
        />
      </el-form-item>
    </el-form>
    <template #footer>
      <div class="flex justify-end gap-[8px]">
        <el-button @click="visible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">保存</el-button>
      </div>
    </template>
  </el-dialog>
</template>
