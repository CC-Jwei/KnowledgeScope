import { reactive } from 'vue'

import type { LoginRequest, RegisterRequest, TokenResponse, UserPublic } from '@knowledgescope/shared'
import { ApiPaths } from '@knowledgescope/shared'

import { apiRequest } from '@/api/http'
import { ACCESS_TOKEN_STORAGE_KEY } from '@/constants/auth'

// 当前登录态，用在路由守卫、顶栏与 Bearer 头
export const authState = reactive({
  accessToken: localStorage.getItem(ACCESS_TOKEN_STORAGE_KEY),
  user: null as UserPublic | null,
  initialized: false,
})

// 把 TokenResponse 写入 localStorage 与内存态，用在登录/注册成功
export function applyTokenResponse(token: TokenResponse): void {
  authState.accessToken = token.accessToken
  localStorage.setItem(ACCESS_TOKEN_STORAGE_KEY, token.accessToken)
}

// 读取当前 Bearer Token，用在 REST/SSE 鉴权
export function getAccessToken(): string | null {
  return authState.accessToken
}

// 清空本地登录态，用在退出与 401
export function clearAuthState(): void {
  authState.accessToken = null
  authState.user = null
  localStorage.removeItem(ACCESS_TOKEN_STORAGE_KEY)
}

// 手机号+密码登录，用在登录页提交
export async function login(payload: LoginRequest): Promise<void> {
  const token = await apiRequest<TokenResponse>(ApiPaths.authLogin(), {
    method: 'POST',
    body: payload,
    skipAuth: true,
  })
  applyTokenResponse(token)
  await fetchCurrentUser()
}

// 注册并自动登录，用在注册页提交
export async function register(payload: RegisterRequest): Promise<void> {
  const token = await apiRequest<TokenResponse>(ApiPaths.authRegister(), {
    method: 'POST',
    body: payload,
    skipAuth: true,
  })
  applyTokenResponse(token)
  await fetchCurrentUser()
}

// 拉取当前用户资料，用在启动恢复与登录后
export async function fetchCurrentUser(): Promise<UserPublic> {
  const user = await apiRequest<UserPublic>(ApiPaths.authMe())
  authState.user = user
  return user
}

// 首次启动时若已有 Token 则恢复用户，用在 main.ts 初始化
export async function initializeAuth(): Promise<void> {
  if (authState.initialized) {
    return
  }
  if (!authState.accessToken) {
    authState.initialized = true
    return
  }
  try {
    await fetchCurrentUser()
  } catch {
    clearAuthState()
  } finally {
    authState.initialized = true
  }
}
