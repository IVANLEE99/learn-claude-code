// 路由定义 + 导航守卫

import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '../views/LoginView.vue'
import RegisterView from '../views/RegisterView.vue'
import HomeView from '../views/HomeView.vue'
import SettingsView from '../views/SettingsView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.VITE_BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: LoginView,
      meta: { requiresAuth: false },
    },
    {
      path: '/register',
      name: 'register',
      component: RegisterView,
      meta: { requiresAuth: false },
    },
    {
      path: '/',
      name: 'home',
      component: HomeView,
      meta: { requiresAuth: true },
    },
    {
      path: '/settings',
      name: 'settings',
      component: SettingsView,
      meta: { requiresAuth: true },
    },
  ],
})

// 导航守卫
router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem('token')
  const isLoggedIn = !!token

  if (to.meta.requiresAuth && !isLoggedIn) {
    // 未登录访问受保护路由，重定向到登录页
    next({ name: 'login' })
  } else if (!to.meta.requiresAuth && isLoggedIn && (to.name === 'login' || to.name === 'register')) {
    // 已登录访问登录/注册页，重定向到首页
    next({ name: 'home' })
  } else {
    next()
  }
})

export default router
