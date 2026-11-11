import { createRouter, createWebHistory } from 'vue-router'

import AppLayout from '@/layouts/AppLayout.vue'
import { authState } from '@/stores/auth'

// 应用路由表，用在 main.ts 注册；业务页需登录
const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/AuthView.vue'),
      meta: { title: '登录 / 注册', public: true },
    },
    {
      path: '/',
      component: AppLayout,
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          name: 'workspace-list',
          component: () => import('@/views/WorkspaceListView.vue'),
          meta: { title: '知识空间', requiresAuth: true },
        },
        {
          path: 'workspaces/:workspaceId',
          name: 'workspace-detail',
          component: () => import('@/views/WorkspaceDetailView.vue'),
          meta: { title: '空间详情', requiresAuth: true },
        },
        {
          path: 'workspaces/:workspaceId/chat',
          name: 'workspace-chat',
          component: () => import('@/views/ConversationView.vue'),
          meta: { title: '会话问答', requiresAuth: true },
        },
        {
          path: 'model-profiles',
          name: 'model-profiles',
          component: () => import('@/views/ModelProfilesView.vue'),
          meta: { title: '模型设置', requiresAuth: true },
        },
      ],
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: '/',
    },
  ],
})

router.beforeEach((to) => {
  // 是否命中需登录路由，用在守卫跳转
  const requiresAuth = to.matched.some((record) => record.meta.requiresAuth)
  // 是否公开路由，用在外层 matched 含鉴权时识别登录页
  const isPublic = to.matched.some((record) => record.meta.public)

  if (!isPublic && requiresAuth && !authState.accessToken) {
    return {
      name: 'login',
      query: { redirect: to.fullPath },
    }
  }

  if (to.name === 'login' && authState.accessToken) {
    return { name: 'workspace-list' }
  }

  return true
})

router.afterEach((to) => {
  // 路由 meta 标题，用在 document.title
  const pageTitle = typeof to.meta.title === 'string' ? to.meta.title : '知域'
  document.title = `${pageTitle} · 知域 KnowledgeScope`
})

export default router
