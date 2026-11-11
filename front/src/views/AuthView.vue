<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'

import type { LoginRequest, RegisterRequest } from '@knowledgescope/shared'

import {
  PASSWORD_MAX_LENGTH,
  PASSWORD_MIN_LENGTH,
  PHONE_MAX_LENGTH,
} from '@/constants/auth'
import { login, register } from '@/stores/auth'
import { getErrorMessage } from '@/utils/error'

// 路由实例，用在登录成功后跳转
const router = useRouter()
// 当前路由，用在 redirect 回跳
const route = useRoute()

// 当前是登录还是注册，用在切换表单
const mode = ref<'login' | 'register'>('login')
// 提交中，用在按钮 loading
const submitting = ref(false)
// 表单引用，用在校验
const formRef = ref<FormInstance>()
// 登录/注册表单字段
const form = reactive({
  phone: '',
  password: '',
  confirmPassword: '',
})

// 表单校验规则，用在 el-form
const rules: FormRules = {
  phone: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    {
      validator: (_rule, value: string, callback) => {
        // 去空白手机号，用在格式校验
        const trimmed = String(value || '').trim()
        if (!/^1\d{10}$/.test(trimmed)) {
          callback(new Error('请输入 11 位中国大陆手机号'))
          return
        }
        callback()
      },
      trigger: 'blur',
    },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    {
      validator: (_rule, value: string, callback) => {
        if (mode.value === 'register') {
          if (!value || value.length < PASSWORD_MIN_LENGTH) {
            callback(new Error(`密码至少 ${PASSWORD_MIN_LENGTH} 位`))
            return
          }
          if (value.length > PASSWORD_MAX_LENGTH) {
            callback(new Error(`密码最长 ${PASSWORD_MAX_LENGTH} 位`))
            return
          }
        }
        callback()
      },
      trigger: 'blur',
    },
  ],
  confirmPassword: [
    {
      validator: (_rule, value: string, callback) => {
        if (mode.value !== 'register') {
          callback()
          return
        }
        if (value !== form.password) {
          callback(new Error('两次输入的密码不一致'))
          return
        }
        callback()
      },
      trigger: 'blur',
    },
  ],
}

// 切换登录/注册并清掉确认密码，用在 Tab 切换
function switchMode(next: 'login' | 'register'): void {
  mode.value = next
  form.confirmPassword = ''
}

// 提交登录或注册，用在表单确认按钮
async function handleSubmit(): Promise<void> {
  if (!formRef.value) {
    return
  }
  // 校验结果，用在阻止无效请求
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) {
    return
  }

  // 去空白手机号，用在请求体
  const phone = form.phone.trim()
  // 登录密码，用在请求体
  const password = form.password

  submitting.value = true
  try {
    if (mode.value === 'register') {
      const payload: RegisterRequest = { phone, password }
      await register(payload)
      ElMessage.success('注册成功，已进入知识空间')
    } else {
      const payload: LoginRequest = { phone, password }
      await login(payload)
      ElMessage.success('登录成功')
    }

    // 登录前想去的地址，用在 redirect 回跳
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/'
    void router.push(redirect)
  } catch (error) {
    ElMessage.error(getErrorMessage(error, '认证失败'))
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="flex min-h-screen min-w-[800px] items-center justify-center bg-[#F5F7FA] px-[24px] py-[48px]">
    <div class="w-full max-w-[420px] rounded-[16px] bg-white p-[32px] shadow-sm">
      <div class="mb-[24px]">
        <div class="text-2xl text-[#111827]">知域 KnowledgeScope</div>
        <div class="mt-[8px] text-sm text-[#6B7280]">
          手机号 + 密码登录；空间按当前用户隔离
        </div>
      </div>

      <div class="mb-[16px] flex gap-[8px]">
        <div
          class="flex-1 cursor-pointer rounded-[8px] py-[10px] text-center text-sm transition-colors"
          :class="mode === 'login' ? 'bg-[#2563EB] text-white' : 'bg-[#F3F4F6] text-[#4B5563] hover:bg-[#E5E7EB]'"
          @click="switchMode('login')"
        >
          登录
        </div>
        <div
          class="flex-1 cursor-pointer rounded-[8px] py-[10px] text-center text-sm transition-colors"
          :class="mode === 'register' ? 'bg-[#2563EB] text-white' : 'bg-[#F3F4F6] text-[#4B5563] hover:bg-[#E5E7EB]'"
          @click="switchMode('register')"
        >
          注册
        </div>
      </div>

      <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
        <el-form-item label="手机号" prop="phone">
          <el-input
            v-model="form.phone"
            :maxlength="PHONE_MAX_LENGTH"
            placeholder="11 位中国大陆手机号"
            autocomplete="username"
          />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input
            v-model="form.password"
            type="password"
            show-password
            :maxlength="PASSWORD_MAX_LENGTH"
            :placeholder="mode === 'register' ? `至少 ${PASSWORD_MIN_LENGTH} 位` : '登录密码'"
            autocomplete="current-password"
            @keyup.enter="handleSubmit"
          />
        </el-form-item>
        <el-form-item v-if="mode === 'register'" label="确认密码" prop="confirmPassword">
          <el-input
            v-model="form.confirmPassword"
            type="password"
            show-password
            :maxlength="PASSWORD_MAX_LENGTH"
            autocomplete="new-password"
            @keyup.enter="handleSubmit"
          />
        </el-form-item>
        <el-button
          type="primary"
          class="w-full"
          :loading="submitting"
          @click="handleSubmit"
        >
          {{ mode === 'register' ? '注册并登录' : '登录' }}
        </el-button>
      </el-form>
    </div>
  </div>
</template>
