// 认证相关 composable

import { useAuthStore } from '../stores/auth.store'
import { useRouter } from 'vue-router'

export function useAuth() {
  const authStore = useAuthStore()
  const router = useRouter()

  async function login(email: string, password: string) {
    await authStore.login(email, password)
    router.push({ name: 'home' })
  }

  async function register(email: string, password: string, nickname: string) {
    await authStore.register(email, password, nickname)
    router.push({ name: 'home' })
  }

  function logout() {
    authStore.logout()
    router.push({ name: 'login' })
  }

  return {
    isLoggedIn: authStore.isLoggedIn,
    user: authStore.user,
    login,
    register,
    logout,
  }
}
