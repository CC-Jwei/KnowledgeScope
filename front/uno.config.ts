import { defineConfig, presetAttributify, presetUno } from 'unocss'

// UnoCSS 配置，用在 Vite 插件生成原子类
export default defineConfig({
  presets: [presetUno(), presetAttributify()],
  shortcuts: {
    // 隐藏滚动条但保留滚动，用在列表横向溢出区域
    'scrollbar-hide':
      '[-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden',
  },
})
