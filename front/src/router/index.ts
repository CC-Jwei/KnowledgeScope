import { createRouter, createWebHistory } from 'vue-router'

import AppLayout from '@/layouts/AppLayout.vue'

// 应用路由表，用在 main.ts 注册
const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      component: AppLayout,
      children: [
        {
          path: '',
          name: 'workspace-list',
          component: () => import('@/views/WorkspaceListView.vue'),
          meta: { title: '知识空间' },
        },
        {
          path: 'workspaces/:workspaceId',
          name: 'workspace-detail',
          component: () => import('@/views/WorkspaceDetailView.vue'),
          meta: { title: '空间详情' },
        },
      ],
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: '/',
    },
  ],
})

router.afterEach((to) => {
  // 路由 meta 标题，用在 document.title
  const pageTitle = typeof to.meta.title === 'string' ? to.meta.title : '知域'
  document.title = `${pageTitle} · 知域 KnowledgeScope`
})

export default router
