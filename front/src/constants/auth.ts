// localStorage 中 Access Token 的键名，用在登录态持久化
export const ACCESS_TOKEN_STORAGE_KEY = 'knowledgescope.access_token'

// 手机号表单最大长度，对齐 backend PHONE_MAX_LENGTH，用在登录注册输入
export const PHONE_MAX_LENGTH = 11

// 密码表单最短长度，对齐 backend RegisterRequest min_length，用在注册校验
export const PASSWORD_MIN_LENGTH = 6

// 密码表单最大长度，对齐 backend schema max_length，用在登录注册校验
export const PASSWORD_MAX_LENGTH = 128
