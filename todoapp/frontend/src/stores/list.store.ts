// 列表状态管理

import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as listApi from '../api/list.api'

export interface TodoList {
  id: string
  name: string
  color: string
  position: number
  todoCount: number
  createdAt: string
  updatedAt: string
}

export const useListStore = defineStore('list', () => {
  const lists = ref<TodoList[]>([])
  const activeListId = ref<string | null>(null)

  async function fetchLists() {
    lists.value = await listApi.getLists()
    // 如果没有选中列表且有列表存在，默认选中第一个
    if (!activeListId.value && lists.value.length > 0) {
      activeListId.value = lists.value[0].id
    }
  }

  async function createList(name: string, color: string) {
    const newList = await listApi.createList({ name, color })
    lists.value.push(newList)
    return newList
  }

  async function updateList(id: string, data: { name?: string; color?: string }) {
    const updated = await listApi.updateList(id, data)
    const index = lists.value.findIndex((l) => l.id === id)
    if (index !== -1) {
      lists.value[index] = updated
    }
    return updated
  }

  async function deleteList(id: string) {
    await listApi.deleteList(id)
    lists.value = lists.value.filter((l) => l.id !== id)
    if (activeListId.value === id) {
      activeListId.value = lists.value.length > 0 ? lists.value[0].id : null
    }
  }

  function setActiveList(id: string | null) {
    activeListId.value = id
  }

  return {
    lists,
    activeListId,
    fetchLists,
    createList,
    updateList,
    deleteList,
    setActiveList,
  }
})
