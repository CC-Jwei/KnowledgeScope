// API 基址（开发默认空串走 Vite 代理），用在所有 REST 请求拼 URL
const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/+$/, '')

export class ApiError extends Error {
  // HTTP 状态码，用在调用方按状态分支（如 404 跳转）
  readonly status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

// 拼出完整请求 URL，用在 apiRequest
export function buildApiUrl(path: string): string {
  if (path.startsWith('http://') || path.startsWith('https://')) {
    return path
  }
  // 保证 path 以 / 开头，用在与基址拼接
  const normalizedPath = path.startsWith('/') ? path : `/${path}`
  return `${API_BASE_URL}${normalizedPath}`
}

// 解析 FastAPI 错误体 detail，用在 ApiError 文案
function extractDetailMessage(payload: unknown): string | null {
  if (!payload || typeof payload !== 'object') {
    return null
  }

  // FastAPI 常见 { detail: string | array }
  const detail = (payload as { detail?: unknown }).detail
  if (typeof detail === 'string' && detail.trim()) {
    return detail
  }
  if (Array.isArray(detail) && detail.length > 0) {
    // 校验错误数组首项，用在 422 提示
    const first = detail[0] as { msg?: unknown }
    if (typeof first?.msg === 'string' && first.msg.trim()) {
      return first.msg
    }
  }
  return null
}

type ApiRequestOptions = Omit<RequestInit, 'body'> & {
  body?: unknown
}

// 统一 JSON 请求封装，用在 workspaces/sources API 模块
export async function apiRequest<T>(path: string, options: ApiRequestOptions = {}): Promise<T> {
  // 请求头，用在 JSON 读写
  const headers = new Headers(options.headers)
  if (!headers.has('Accept')) {
    headers.set('Accept', 'application/json')
  }

  // 序列化后的 body，用在 fetch
  let body: BodyInit | undefined
  if (options.body !== undefined) {
    headers.set('Content-Type', 'application/json')
    body = JSON.stringify(options.body)
  }

  // 原始响应，用在状态码与正文解析
  const response = await fetch(buildApiUrl(path), {
    ...options,
    headers,
    body,
  })

  if (response.status === 204) {
    return undefined as T
  }

  // 响应文本，用在空 body 与 JSON 解析兜底
  const rawText = await response.text()
  // 解析后的 JSON（可能为空），用在成功返回或错误 detail
  let payload: unknown = undefined
  if (rawText) {
    try {
      payload = JSON.parse(rawText) as unknown
    } catch {
      payload = rawText
    }
  }

  if (!response.ok) {
    // 优先使用后端 detail，否则回退状态文案
    const message =
      extractDetailMessage(payload) ||
      (typeof payload === 'string' && payload.trim() ? payload : `HTTP ${response.status}`)
    throw new ApiError(response.status, message)
  }

  return payload as T
}
