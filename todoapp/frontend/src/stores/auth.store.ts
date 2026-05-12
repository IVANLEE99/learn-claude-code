// 认证状态管理

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as authApi from '../api/auth.api'
import * as userApi from '../api/user.api'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('token'))
  const user = ref<{ id: string; email: string; nickname: string; createdAt: string } | null>(null)

  const isLoggedIn = computed(() => !!token.value)

  async function login(email: string, password: string) {
    const data = await authApi.login({ email, password })
    token.value = data.token
    user.value = data.user
    localStorage.setItem('token', data.token)
  }

  async function register(email: string, password: string, nickname: string) {
    const data = await authApi.register({ email, password, nickname })
    token.value = data.token
    user.value = data.user
    localStorage.setItem('token', data.token)
  }

  async function fetchUser() {
    const data = await userApi.getMe()
    user.value = data
  }

  async function updateNickname(nickname: string) {
    const data = await userApi.updateNickname({ nickname })
    user.value = data
  }

  async function changePassword(oldPassword: string, newPassword: string) {
    await userApi.changePassword({ oldPassword, newPassword })
  }

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem('token')
  }

  return {
    token,
    user,
    isLoggedIn,
    login,
    register,
    fetchUser,
    updateNickname,
    changePassword,
    logout,
  }
})
