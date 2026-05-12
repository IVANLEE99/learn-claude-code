<script setup lang="ts">
import { ref } from 'vue'
import { useListStore } from '../stores/list.store'
import { useTodoStore } from '../stores/todo.store'

const listStore = useListStore()
const todoStore = useTodoStore()

const title = ref('')
const description = ref('')
const listId = ref('')
const priority = ref('medium')
const isExpanded = ref(false)

const PRIORITIES = [
  { key: 'high', label: '高', color: 'var(--color-priority-high)' },
  { key: 'medium', label: '中', color: 'var(--color-priority-medium)' },
  { key: 'low', label: '低', color: 'var(--color-priority-low)' },
]

// 初始化选中列表
if (listStore.activeListId) {
  listId.value = listStore.activeListId
}

async function handleSubmit() {
  if (!title.value.trim() || !listId.value) return

  try {
    await todoStore.createTodo({
      title: title.value.trim(),
      description: description.value.trim() || undefined,
      listId: listId.value,
      priority: priority.value,
    })
    title.value = ''
    description.value = ''
    priority.value = 'medium'
    isExpanded.value = false
  } catch {
    // 错误由 axios 拦截器处理
  }
}

function expandForm() {
  isExpanded.value = true
}
</script>

<template>
  <div class="todo-form">
    <form @submit.prevent="handleSubmit">
      <div class="form-main">
        <input
          v-model="title"
          class="form-input"
          placeholder="添加新待办..."
          @focus="expandForm"
        />
        <button type="submit" class="btn-add" :disabled="!title.trim() || !listId">
          +
        </button>
      </div>

      <div v-if="isExpanded" class="form-details">
        <textarea
          v-model="description"
          class="form-textarea"
          placeholder="描述（可选）"
          rows="2"
        ></textarea>

        <div class="form-row">
          <select v-model="listId" class="form-select">
            <option value="" disabled>选择列表</option>
            <option v-for="list in listStore.lists" :key="list.id" :value="list.id">
              {{ list.name }}
            </option>
          </select>

          <div class="priority-picker">
            <button
              v-for="p in PRIORITIES"
              :key="p.key"
              type="button"
              class="priority-btn"
              :class="{ 'priority-btn--active': priority === p.key }"
              :style="{ borderColor: priority === p.key ? p.color : 'var(--color-border)' }"
              @click="priority = p.key"
            >
              {{ p.label }}
            </button>
          </div>
        </div>
      </div>
    </form>
  </div>
</template>

<style scoped>
.todo-form {
  background: var(--color-bg-card);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-sm);
  padding: var(--spacing-base);
  margin-bottom: var(--spacing-base);
}

.form-main {
  display: flex;
  gap: var(--spacing-sm);
  align-items: center;
}

.form-input {
  flex: 1;
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

.form-input::placeholder {
  color: var(--color-text-tertiary);
}

.btn-add {
  width: var(--size-clickable);
  height: var(--size-clickable);
  border: none;
  background: var(--color-brand-primary);
  color: var(--color-text-inverse);
  font-size: var(--font-size-lg);
  border-radius: var(--radius-sm);
  cursor: pointer;
  flex-shrink: 0;
  transition: background-color var(--duration-fast) var(--ease-out);
}

.btn-add:hover:not(:disabled) {
  background: var(--color-brand-primary-dark);
}

.btn-add:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.form-details {
  margin-top: var(--spacing-base);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-base);
}

.form-textarea {
  width: 100%;
  padding: var(--spacing-sm) var(--spacing-base);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-bg-card);
  color: var(--color-text-primary);
  font-size: var(--font-size-base);
  font-family: var(--font-family);
  resize: vertical;
}

.form-textarea:focus {
  outline: none;
  border-color: var(--color-brand-primary);
  box-shadow: var(--shadow-focus);
}

.form-row {
  display: flex;
  gap: var(--spacing-base);
  align-items: center;
}

.form-select {
  flex: 1;
  height: var(--size-clickable);
  padding: 0 var(--spacing-base);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-bg-card);
  color: var(--color-text-primary);
  font-size: var(--font-size-base);
  font-family: var(--font-family);
}

.form-select:focus {
  outline: none;
  border-color: var(--color-brand-primary);
  box-shadow: var(--shadow-focus);
}

.priority-picker {
  display: flex;
  gap: var(--spacing-xs);
}

.priority-btn {
  height: 32px;
  padding: 0 var(--spacing-md);
  border: 2px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-bg-card);
  font-size: var(--font-size-sm);
  font-family: var(--font-family);
  cursor: pointer;
  transition: border-color var(--duration-fast) var(--ease-out);
}

.priority-btn--active {
  font-weight: var(--font-weight-medium);
}
</style>
