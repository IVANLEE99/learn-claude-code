// axios 实例 -- 所有 API 调用必须通过此实例
// baseURL 来自环境变量，禁止硬编码 /api/... 路径

import axios from 'axios'

const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE,
  headers: { 'Content-Type': 'application/json' },
})

// 请求拦截器：自动附加 JWT
client.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截器：401 时清除 token 并跳转登录
client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      // 使用环境变量构建登录路径，避免硬编码
      window.location.href = `${import.meta.env.VITE_BASE_URL}login`
    }
    return Promise.reject(error)
  },
)

export default client
