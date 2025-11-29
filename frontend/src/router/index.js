import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('../views/Register.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/forgot-password',
    name: 'ForgotPassword',
    component: () => import('../views/ForgotPassword.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/reset-password/:token',
    name: 'ResetPassword',
    component: () => import('../views/ResetPassword.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/auth/google/callback',
    name: 'GoogleCallback',
    component: () => import('../views/GoogleCallback.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/',
    component: () => import('../components/AppLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'Dashboard',
        component: () => import('../views/Dashboard.vue'),
      },
      {
        path: 'profile',
        name: 'Profile',
        component: () => import('../views/Profile.vue'),
      },
      {
        path: 'teams',
        name: 'TeamList',
        component: () => import('../views/TeamList.vue'),
      },
      {
        path: 'teams/:teamId',
        name: 'TeamDetail',
        component: () => import('../views/TeamDetail.vue'),
      },
      {
        path: 'projects/:projectId',
        name: 'KanbanBoard',
        component: () => import('../views/KanbanBoard.vue'),
      },
      {
        path: 'projects/:projectId/issues/:issueId',
        name: 'IssueDetail',
        component: () => import('../views/IssueDetail.vue'),
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// Navigation guard
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth)
  
  if (requiresAuth && !authStore.isAuthenticated) {
    next({ name: 'Login', query: { redirect: to.fullPath } })
  } else if (!requiresAuth && authStore.isAuthenticated && (to.name === 'Login' || to.name === 'Register')) {
    next({ name: 'Dashboard' })
  } else {
    next()
  }
})

export default router
