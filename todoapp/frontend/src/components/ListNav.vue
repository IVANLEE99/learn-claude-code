<script setup lang="ts">
import { ref } from 'vue'
import { useListStore, type TodoList } from '../stores/list.store'
import ListItem from './ListItem.vue'

const listStore = useListStore()
const showNewListForm = ref(false)
const newListName = ref('')
const newListColor = ref('#4A90D9')
const editingList = ref<TodoList | null>(null)
const editName = ref('')

const PRESET_COLORS = ['#E74C3C', '#F39C12', '#27AE60', '#3498DB', '#9B59B6', '#4A90D9']

async function handleCreateList() {
  if (!newListName.value.trim()) return
  try {
    await listStore.createList(newListName.value.trim(), newListColor.value)
    newListName.value = ''
    showNewListForm.value = false
  } catch {
    // 错误由 axios 拦截器处理
  }
}

function startEdit(list: TodoList) {
  editingList.value = list
  editName.value = list.name
}

async function handleUpdateList() {
  if (!editingList.value || !editName.value.trim()) return
  try {
    await listStore.updateList(editingList.value.id, { name: editName.value.trim() })
    editingList.value = null
  } catch {
    // 错误由 axios 拦截器处理
  }
}

async function handleDeleteList(list: TodoList) {
  if (!confirm(`确定删除列表"${list.name}"及其下所有待办吗？`)) return
  try {
    await listStore.deleteList(list.id)
  } catch {
    // 错误由 axios 拦截器处理
  }
}
</script>

<template>
  <nav class="list-nav" aria-label="待办列表">
    <div class="list-nav-header">
      <h2 class="list-nav-title">我的列表</h2>
      <button class="btn-add" @click="showNewListForm = !showNewListForm">+</button>
    </div>

    <!-- 新建列表表单 -->
    <div v-if="showNewListForm" class="new-list-form">
      <input
        v-model="newListName"
        class="form-input"
        placeholder="列表名称"
        @keyup.enter="handleCreateList"
      />
      <div class="color-picker">
        <button
          v-for="c in PRESET_COLORS"
          :key="c"
          class="color-dot"
          :class="{ 'color-dot--active': newListColor === c }"
          :style="{ backgroundColor: c }"
          @click="newListColor = c"
        ></button>
      </div>
      <div class="form-actions">
        <button class="btn btn-sm btn-primary" @click="handleCreateList">创建</button>
        <button class="btn btn-sm btn-secondary" @click="showNewListForm = false">取消</button>
      </div>
    </div>

    <!-- 编辑列表表单 -->
    <div v-if="editingList" class="edit-list-form">
      <input
        v-model="editName"
        class="form-input"
        placeholder="列表名称"
        @keyup.enter="handleUpdateList"
      />
      <div class="form-actions">
        <button class="btn btn-sm btn-primary" @click="handleUpdateList">保存</button>
        <button class="btn btn-sm btn-secondary" @click="editingList = null">取消</button>
      </div>
    </div>

    <!-- 列表列表 -->
    <div class="list-nav-items">
      <ListItem
        v-for="list in listStore.lists"
        :key="list.id"
        :list="list"
        :is-active="listStore.activeListId === list.id"
        @select="listStore.setActiveList(list.id)"
        @edit="startEdit(list)"
        @delete="handleDeleteList(list)"
      />
    </div>
  </nav>
</template>

<style scoped>
.list-nav {
  height: 100%;
  overflow-y: auto;
}

.list-nav-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-base);
  border-bottom: 1px solid var(--color-border-light);
}

.list-nav-title {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
}

.btn-add {
  width: 32px;
  height: 32px;
  border: none;
  background: var(--color-brand-primary);
  color: var(--color-text-inverse);
  font-size: var(--font-size-lg);
  border-radius: var(--radius-full);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color var(--duration-fast) var(--ease-out);
}

.btn-add:hover {
  background: var(--color-brand-primary-dark);
}

.new-list-form,
.edit-list-form {
  padding: var(--spacing-base);
  border-bottom: 1px solid var(--color-border-light);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.form-input {
  height: var(--size-clickable);
  padding: 0 var(--spacing-base);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-bg-card);
  color: var(--color-text-primary);
  font-size: var(--font-size-base);
  font-family: var(--font-family);
}

.form-input:focus {
  outline: none;
  border-color: var(--color-brand-primary);
  box-shadow: var(--shadow-focus);
}

.color-picker {
  display: flex;
  gap: var(--spacing-sm);
  flex-wrap: wrap;
}

.color-dot {
  width: 24px;
  height: 24px;
  border-radius: var(--radius-full);
  border: 2px solid transparent;
  cursor: pointer;
  transition: border-color var(--duration-fast) var(--ease-out);
}

.color-dot--active {
  border-color: var(--color-text-primary);
}

.form-actions {
  display: flex;
  gap: var(--spacing-sm);
}

.btn {
  border: none;
  border-radius: var(--radius-sm);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  font-family: var(--font-family);
  cursor: pointer;
  transition: background-color var(--duration-fast) var(--ease-out);
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-sm {
  height: 32px;
  padding: 0 var(--spacing-base);
}

.btn-primary {
  background: var(--color-brand-primary);
  color: var(--color-text-inverse);
}

.btn-primary:hover {
  background: var(--color-brand-primary-dark);
}

.btn-secondary {
  background: var(--color-bg-hover);
  color: var(--color-text-secondary);
}

.list-nav-items {
  padding: var(--spacing-sm) 0;
}
</style>
