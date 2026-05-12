// 待办 API -- GET /todos, POST /todos, PUT /todos/:id, PATCH /todos/:id/toggle, DELETE /todos/:id

import client from './client'

export async function getTodos(params?: { listId?: string; status?: string; keyword?: string }) {
  const res = await client.get('/todos', { params })
  return res.data.data
}

export async function createTodo(data: { title: string; description?: string; listId: string; priority?: string }) {
  const res = await client.post('/todos', data)
  return res.data.data
}

export async function updateTodo(id: string, data: { title?: string; description?: string; priority?: string; listId?: string }) {
  const res = await client.put(`/todos/${id}`, data)
  return res.data.data
}

export async function toggleTodo(id: string) {
  const res = await client.patch(`/todos/${id}/toggle`)
  return res.data.data
}

export async function deleteTodo(id: string) {
  const res = await client.delete(`/todos/${id}`)
  return res.data.data
}
