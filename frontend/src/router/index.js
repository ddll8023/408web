/**
 * Vue Router 路由配置
 * 配置路由和路由守卫
 * 遵循KISS原则：简单的路由配置
 * 
 * Source: Vue Router 4.3.2 官方文档
 */
import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

// 路由配置
const routes = [
  {
    path: '/',
    redirect: '/exam' // 重定向到真题首页
  },
  {
    path: '/login',
    component: () => import('@/views/user/Login.vue')
  },
  {
    path: '/register',
    component: () => import('@/views/user/Register.vue')
  },
  {
    path: '/user/center',
    component: () => import('@/views/user/UserCenter.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/exam',
    component: () => import('@/views/user/ExamIndex.vue'),
    meta: { keepAlive: true }
  },
  {
    path: '/exam/classify',
    component: () => import('@/views/user/ExamClassify.vue'),
    meta: { keepAlive: true }
  },
  {
    path: '/exam/:year',
    component: () => import('@/views/user/ExamList.vue'),
    meta: { keepAlive: true }
  },

  {
    path: '/manage/subject',
    component: () => import('@/views/admin/SubjectManage.vue'),
    meta: { requiresAuth: true, requiresAdmin: true }
  },
  {
    path: '/manage/exam',
    component: () => import('@/views/admin/ExamManage.vue'),
    meta: { requiresAuth: true, requiresAdmin: true, keepAlive: true }
  },
  {
    path: '/manage/category',
    component: () => import('@/views/admin/CategoryManage.vue'),
    meta: { requiresAuth: true, requiresAdmin: true }
  },
  {
    path: '/manage/exam-category',
    component: () => import('@/views/admin/ExamCategoryStats.vue'),
    meta: { requiresAuth: true, requiresAdmin: true }
  },
  {
    path: '/manage/image',
    component: () => import('@/views/admin/ImageManage.vue'),
    meta: { requiresAuth: true, requiresAdmin: true }
  },
  // 模拟题相关路由
  {
    path: '/mock',
    component: () => import('@/views/user/MockClassify.vue'),
    meta: { keepAlive: true }
  },
  {
    path: '/mock/:source',
    component: () => import('@/views/user/MockList.vue'),
    meta: { keepAlive: true }
  },

  {
    path: '/manage/mock',
    component: () => import('@/views/admin/MockManage.vue'),
    meta: { requiresAuth: true, requiresAdmin: true, keepAlive: true }
  }
]

// 创建路由实例
const router = createRouter({
  history: createWebHistory(),
  routes
})

/**
 * 全局前置守卫
 * 验证Token和权限
 */
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()

  // 检查路由是否需要认证
  if (to.meta.requiresAuth) {
    // 需要认证，检查是否已登录
    if (authStore.isLoggedIn()) {
      // 检查是否需要管理员权限
      if (to.meta.requiresAdmin) {
        if (authStore.isAdmin()) {
          next()
        } else {
          // 不是管理员，拒绝访问
          alert('权限不足，需要管理员权限')
          next({ path: '/' })
        }
      } else {
        next()
      }
    } else {
      // 未登录，跳转到登录页
      next({
        path: '/login',
        query: { redirect: to.fullPath }
      })
    }
  } else {
    // 不需要认证，直接放行
    next()
  }
})

export default router

