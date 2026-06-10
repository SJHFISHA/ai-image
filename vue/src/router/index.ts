import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { requiresAuth: false }
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('@/views/RegisterView.vue'),
      meta: { requiresAuth: false }
    },
    {
      path: '/',
      redirect: '/image-generate',
    },
    {
      path: '/dashboard',
      name: 'dashboard',
      component: () => import('@/views/DashboardView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/image-generate',
      name: 'image-generate',
      component: () => import('@/views/HomeView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/points/logs',
      name: 'point-logs',
      component: () => import('@/views/PointLogsView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/tasks',
      name: 'tasks',
      component: () => import('@/views/TaskListView.vue'),
      meta: { requiresAuth: true }
    },
    // ======================== 管理员路由 ========================
    {
      path: '/admin/login',
      name: 'admin-login',
      component: () => import('@/views/admin/AdminLoginView.vue'),
    },
    {
      path: '/admin',
      component: () => import('@/views/admin/AdminLayout.vue'),
      children: [
        {
          path: '',
          redirect: '/admin/model-prices'
        },
        {
          path: 'model-prices',
          name: 'admin-model-prices',
          component: () => import('@/views/admin/ModelPriceView.vue')
        },
        {
          path: 'recharge-packages',
          name: 'admin-recharge-packages',
          component: () => import('@/views/admin/RechargePackageView.vue')
        },
        {
          path: 'recharge-orders',
          name: 'admin-recharge-orders',
          component: () => import('@/views/admin/RechargeOrderView.vue')
        },
        {
          path: 'point-accounts',
          name: 'admin-point-accounts',
          component: () => import('@/views/admin/PointAccountView.vue')
        },
        {
          path: 'point-transactions',
          name: 'admin-point-transactions',
          component: () => import('@/views/admin/PointTransactionView.vue')
        },
        {
          path: 'users',
          name: 'admin-users',
          component: () => import('@/views/admin/UserView.vue')
        },
        {
          path: 'tasks',
          name: 'admin-tasks',
          component: () => import('@/views/admin/GenerationTaskView.vue')
        }
      ]
    }
  ]
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('access_token')
  const adminToken = localStorage.getItem('admin_access_token')

  // 管理员路由守卫：通过路径前缀判断
  if (to.path.startsWith('/admin')) {
    // 已登录管理员访问登录页，跳转到管理后台
    if (to.name === 'admin-login') {
      if (adminToken) {
        next('/admin')
      } else {
        next()
      }
    } else {
      // 其他管理员页面需要登录
      if (!adminToken) {
        next('/admin/login')
      } else {
        next()
      }
    }
    return
  }

  // 普通用户路由守卫
  if (to.meta.requiresAuth && !token) {
    next('/login')
  } else if ((to.name === 'login' || to.name === 'register') && token) {
    next('/')
  } else {
    next()
  }
})

export default router
