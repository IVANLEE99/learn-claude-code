// 列表 API -- GET /lists, POST /lists, PUT /lists/:id, DELETE /lists/:id

import client from './client'

export async function getLists() {
  const res = await client.get('/lists')
  return res.data.data
}

export async function createList(data: { name: string; color: string }) {
  const res = await client.post('/lists', data)
  return res.data.data
}

export async function updateList(id: string, data: { name?: string; color?: string }) {
  const res = await client.put(`/lists/${id}`, data)
  return res.data.data
}

export async function deleteList(id: string) {
  const res = await client.delete(`/lists/${id}`)
  return res.data.data
}
