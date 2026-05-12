// 待办状态管理

import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as todoApi from '../api/todo.api'

export interface Todo {
  id: string
  title: string
  description: string | null
  priority: string
  completed: boolean
  listId: string
  listName: string
  listColor: string
  position: number
  createdAt: string
  updatedAt: string
}

export const useTodoStore = defineStore('todo', () => {
  const todos = ref<Todo[]>([])
  const filterStatus = ref<string>('all')
  const keyword = ref<string>('')

  async function fetchTodos(params?: { listId?: string; status?: string; keyword?: string }) {
    todos.value = await todoApi.getTodos(params)
  }

  async function createTodo(data: { title: string; description?: string; listId: string; priority?: string }) {
    const newTodo = await todoApi.createTodo(data)
    todos.value.unshift(newTodo)
    return newTodo
  }

  async function updateTodo(id: string, data: { title?: string; description?: string; priority?: string; listId?: string }) {
    const updated = await todoApi.updateTodo(id, data)
    const index = todos.value.findIndex((t) => t.id === id)
    if (index !== -1) {
      todos.value[index] = updated
    }
    return updated
  }

  async function toggleTodo(id: string) {
    const updated = await todoApi.toggleTodo(id)
    const index = todos.value.findIndex((t) => t.id === id)
    if (index !== -1) {
      todos.value[index] = updated
    }
    return updated
  }

  async function deleteTodo(id: string) {
    await todoApi.deleteTodo(id)
    todos.value = todos.value.filter((t) => t.id !== id)
  }

  function setFilterStatus(status: string) {
    filterStatus.value = status
  }

  function setKeyword(kw: string) {
    keyword.value = kw
  }

  return {
    todos,
    filterStatus,
    keyword,
    fetchTodos,
    createTodo,
    updateTodo,
    toggleTodo,
    deleteTodo,
    setFilterStatus,
    setKeyword,
  }
})
