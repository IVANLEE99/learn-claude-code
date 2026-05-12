<script setup lang="ts">
import type { Todo } from '../stores/todo.store'

const props = defineProps<{
  todo: Todo
}>()

const emit = defineEmits<{
  toggle: []
  delete: []
  edit: []
}>()

const PRIORITY_COLORS: Record<string, string> = {
  high: 'var(--color-priority-high)',
  medium: 'var(--color-priority-medium)',
  low: 'var(--color-priority-low)',
}

const PRIORITY_LABELS: Record<string, string> = {
  high: '高',
  medium: '中',
  low: '低',
}
</script>

<template>
  <div
    class="todo-card"
    :class="{ 'todo-card--completed': todo.completed }"
    role="listitem"
  >
    <div
      class="priority-bar"
      :style="{ backgroundColor: PRIORITY_COLORS[todo.priority] || PRIORITY_COLORS.medium }"
    ></div>

    <button
      class="todo-checkbox"
      :class="{ 'todo-checkbox--checked': todo.completed }"
      :aria-label="todo.completed ? '标记为未完成' : '标记为完成'"
      @click="emit('toggle')"
    >
      <span v-if="todo.completed" class="checkmark">&#10003;</span>
    </button>

    <div class="todo-content" @click="emit('edit')">
      <div class="todo-title" :class="{ 'todo-title--done': todo.completed }">
        {{ todo.title }}
      </div>
      <div v-if="todo.description" class="todo-description">
        {{ todo.description }}
      </div>
      <div class="todo-meta">
        <span class="todo-list-tag" :style="{ color: todo.listColor }">{{ todo.listName }}</span>
        <span class="todo-priority" :style="{ color: PRIORITY_COLORS[todo.priority] }">
          {{ PRIORITY_LABELS[todo.priority] || '中' }}
        </span>
      </div>
    </div>

    <button class="todo-delete" title="删除" @click="emit('delete')">
      &times;
    </button>
  </div>
</template>

<style scoped>
.todo-card {
  display: flex;
  align-items: flex-start;
  min-height: var(--size-todo-item);
  background: var(--color-bg-card);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-sm);
  overflow: hidden;
  transition: box-shadow var(--duration-fast) var(--ease-out);
}

.todo-card:hover {
  box-shadow: var(--shadow-md);
}

.todo-card--completed {
  opacity: 0.7;
}

.priority-bar {
  width: 3px;
  min-height: 100%;
  flex-shrink: 0;
}

.todo-checkbox {
  width: 22px;
  height: 22px;
  border: 2px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-bg-card);
  cursor: pointer;
  flex-shrink: 0;
  margin: var(--spacing-base) var(--spacing-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: border-color var(--duration-fast) var(--ease-out),
              background-color var(--duration-fast) var(--ease-out);
}

.todo-checkbox:hover {
  border-color: var(--color-brand-primary);
}

.todo-checkbox--checked {
  background: var(--color-success);
  border-color: var(--color-success);
}

.checkmark {
  color: var(--color-text-inverse);
  font-size: 12px;
  font-weight: var(--font-weight-bold);
}

.todo-content {
  flex: 1;
  padding: var(--spacing-base) var(--spacing-sm) var(--spacing-base) 0;
  cursor: pointer;
  min-width: 0;
}

.todo-title {
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
  word-break: break-word;
}

.todo-title--done {
  color: var(--color-text-tertiary);
  text-decoration: line-through;
}

.todo-description {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  margin-top: var(--spacing-xs);
  word-break: break-word;
}

.todo-meta {
  display: flex;
  gap: var(--spacing-md);
  margin-top: var(--spacing-xs);
  font-size: var(--font-size-xs);
}

.todo-list-tag {
  font-weight: var(--font-weight-medium);
}

.todo-priority {
  font-weight: var(--font-weight-medium);
}

.todo-delete {
  width: 32px;
  height: 32px;
  border: none;
  background: none;
  color: var(--color-text-tertiary);
  font-size: var(--font-size-lg);
  cursor: pointer;
  border-radius: var(--radius-sm);
  flex-shrink: 0;
  margin: var(--spacing-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color var(--duration-fast) var(--ease-out),
              background-color var(--duration-fast) var(--ease-out);
}

.todo-delete:hover {
  color: var(--color-danger);
  background: var(--color-danger-light);
}
</style>
