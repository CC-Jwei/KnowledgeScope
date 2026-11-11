<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'

import type { SourceCreateInput, SourceType } from '@knowledgescope/shared'
import {
  CREATABLE_SOURCE_TYPES,
  INITIAL_SOURCE_STATUS,
  SourceTypeValue,
} from '@knowledgescope/shared'

import { createSource } from '@/api/sources'
import { SOURCE_CONTENT_MAX_LENGTH, SOURCE_TITLE_MAX_LENGTH } from '@/constants/ui'
import { SOURCE_TYPE_LABEL } from '@/utils/sourceStatus'
import { getErrorMessage } from '@/utils/error'

const props = defineProps<{
  workspaceId: string
}>()

const emit = defineEmits<{
  created: []
}>()

// 当前投递类型，用在与 content/url 表单切换
const selectedType = ref<SourceType>(SourceTypeValue.PlainText)
// 提交中，用在保存按钮 loading
const submitting = ref(false)
// 表单引用，用在校验与清空
const formRef = ref<FormInstance>()
// 表单字段，用在按类型拼 SourceCreateInput
const form = reactive({
  title: '',
  content: '',
  url: '',
})

// 可投递类型选项，用在类型切换按钮
const typeOptions = CREATABLE_SOURCE_TYPES

// 是否文本类（plain_text / markdown），用在正文必填
const isTextType = computed(
  () =>
    selectedType.value === SourceTypeValue.PlainText ||
    selectedType.value === SourceTypeValue.Markdown,
)

// 是否网页类型，用在 URL 必填
const isWebType = computed(() => selectedType.value === SourceTypeValue.WebPage)

// 表单校验，用在 el-form
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
    {
      validator: (_rule, value: string, callback) => {
        if (!isTextType.value) {
          callback()
          return
        }
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
  url: [
    {
      validator: (_rule, value: string, callback) => {
        if (!isWebType.value) {
          callback()
          return
        }
        // 去空白 URL，用在 scheme 校验
        const trimmed = String(value || '').trim()
        if (!trimmed) {
          callback(new Error('请输入网页 URL'))
          return
        }
        if (!/^https?:\/\/.+/i.test(trimmed)) {
          callback(new Error('仅支持 http/https URL'))
          return
        }
        callback()
      },
      trigger: 'blur',
    },
  ],
}

// 切换来源类型，用在三个类型按钮
function selectType(type: SourceType): void {
  selectedType.value = type
  void formRef.value?.clearValidate()
}

// 提交投递，类型不同拼不同载荷，用在保存按钮
async function handleSubmit(): Promise<void> {
  if (!formRef.value) {
    return
  }
  // 校验结果，用在阻止无效请求
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) {
    return
  }

  // 去空白可选标题，用在请求体
  const title = form.title.trim() || null
  // 创建载荷，用在 POST sources
  let payload: SourceCreateInput

  if (selectedType.value === SourceTypeValue.WebPage) {
    payload = {
      type: SourceTypeValue.WebPage,
      title,
      url: form.url.trim(),
    }
  } else if (selectedType.value === SourceTypeValue.Markdown) {
    payload = {
      type: SourceTypeValue.Markdown,
      title,
      content: form.content.trim(),
    }
  } else {
    payload = {
      type: SourceTypeValue.PlainText,
      title,
      content: form.content.trim(),
    }
  }

  submitting.value = true
  try {
    await createSource(props.workspaceId, payload)
    ElMessage.success(`已投递，当前状态：${INITIAL_SOURCE_STATUS}`)
    form.title = ''
    form.content = ''
    form.url = ''
    formRef.value.resetFields()
    emit('created')
  } catch (error) {
    ElMessage.error(getErrorMessage(error, '投递来源失败'))
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="rounded-[12px] bg-white p-[16px] shadow-sm">
    <div class="mb-[12px] text-lg text-[#111827]">投递来源</div>
    <div class="mb-[12px] text-sm text-[#6B7280]">
      创建后为 pending，入库完成后才可被严格问答检索
    </div>

    <div class="mb-[16px] flex gap-[8px]">
      <div
        v-for="type in typeOptions"
        :key="type"
        class="flex-1 cursor-pointer rounded-[8px] border px-[8px] py-[10px] text-center text-sm transition-colors"
        :class="
          selectedType === type
            ? 'border-[#2563EB] bg-[#EEF2FF] text-[#2563EB]'
            : 'border-[#E5E7EB] text-[#4B5563] hover:bg-[#F9FAFB]'
        "
        @click="selectType(type)"
      >
        {{ SOURCE_TYPE_LABEL[type] }}
      </div>
    </div>

    <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
      <el-form-item label="标题（可选）" prop="title">
        <el-input
          v-model="form.title"
          :maxlength="SOURCE_TITLE_MAX_LENGTH"
          show-word-limit
          placeholder="不填则由服务端生成"
        />
      </el-form-item>

      <el-form-item v-if="isTextType" label="正文" prop="content">
        <el-input
          v-model="form.content"
          type="textarea"
          :rows="10"
          :maxlength="SOURCE_CONTENT_MAX_LENGTH"
          show-word-limit
          :placeholder="
            selectedType === SourceTypeValue.Markdown
              ? '粘贴 Markdown 文本，保留 # 标题等格式'
              : '粘贴一段纯文字资料…'
          "
        />
      </el-form-item>

      <el-form-item v-if="isWebType" label="网页 URL" prop="url">
        <el-input
          v-model="form.url"
          placeholder="https://example.com/article"
        />
        <div class="mt-[6px] text-xs text-[#6B7280]">
          仅单页 http/https，超时或抓取失败会标记 failed
        </div>
      </el-form-item>

      <el-button type="primary" class="w-full" :loading="submitting" @click="handleSubmit">
        保存为来源
      </el-button>
    </el-form>
  </div>
</template>
