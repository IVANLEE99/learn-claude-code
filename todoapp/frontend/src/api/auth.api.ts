// 认证 API -- POST /auth/register, POST /auth/login

import client from './client'

export async function register(data: { email: string; password: string; nickname: string }) {
  const res = await client.post('/auth/register', data)
  return res.data.data
}

export async function login(data: { email: string; password: string }) {
  const res = await client.post('/auth/login', data)
  return res.data.data
}
