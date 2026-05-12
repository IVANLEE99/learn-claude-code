// 用户 API -- GET /users/me, PUT /users/me, PUT /users/me/password

import client from './client'

export async function getMe() {
  const res = await client.get('/users/me')
  return res.data.data
}

export async function updateNickname(data: { nickname: string }) {
  const res = await client.put('/users/me', data)
  return res.data.data
}

export async function changePassword(data: { oldPassword: string; newPassword: string }) {
  const res = await client.put('/users/me/password', data)
  return res.data.data
}
