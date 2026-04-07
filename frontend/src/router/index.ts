import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'Landing',
      component: () => import('@/views/Landing.vue'),
    },
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/Login.vue'),
    },
    {
      path: '/register',
      name: 'Register',
      component: () => import('@/views/Register.vue'),
    },
    {
      path: '/demo',
      name: 'Demo',
      component: () => import('@/views/Demo.vue'),
    },
    {
      path: '/workspace',
      name: 'Workspace',
      component: () => import('@/views/Workspace.vue'),
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          name: 'Dashboard',
          component: () => import('@/views/Dashboard.vue'),
        },
        {
          path: 'contracts',
          name: 'Contracts',
          component: () => import('@/views/Contracts.vue'),
        },
        {
          path: 'upload',
          name: 'Upload',
          component: () => import('@/views/Upload.vue'),
        },
        {
          path: 'review/:id',
          name: 'Review',
          component: () => import('@/views/Review.vue'),
        },
        {
          path: 'review-word/:id',
          name: 'ReviewWord',
          component: () => import('@/views/ReviewWord.vue'),
        },
      ],
    },
  ],
})

router.beforeEach((to) => {
  if (to.meta.requiresAuth) {
    const authStore = useAuthStore()
    if (!authStore.isAuthenticated) {
      return { name: 'Login' }
    }
  }
})

export default router
