import path from 'node:path'
import { fileURLToPath, URL } from 'node:url'

import vue from '@vitejs/plugin-vue'
import UnoCSS from 'unocss/vite'
import { defineConfig, loadEnv } from 'vite'

// front 目录绝对路径，用在 resolve.alias 相对定位 shared
const frontDir = fileURLToPath(new URL('.', import.meta.url))

// Vite 配置：别名、代理与插件，用在本地开发与构建
export default defineConfig(({ mode }) => {
  // 当前模式环境变量，用在读取代理目标
  const env = loadEnv(mode, frontDir, '')
  // 后端代理目标，用在 /api 与 /health 转发
  const proxyTarget = env.VITE_PROXY_TARGET || 'http://127.0.0.1:8000'

  return {
    plugins: [vue(), UnoCSS()],
    resolve: {
      alias: {
        '@': path.resolve(frontDir, 'src'),
        '@knowledgescope/shared': path.resolve(frontDir, '../shared/src/index.ts'),
      },
    },
    server: {
      host: '0.0.0.0',
      port: 5173,
      proxy: {
        '/api': {
          target: proxyTarget,
          changeOrigin: true,
        },
        '/health': {
          target: proxyTarget,
          changeOrigin: true,
        },
      },
    },
  }
})
