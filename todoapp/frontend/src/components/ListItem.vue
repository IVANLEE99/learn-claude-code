<script setup lang="ts">
import type { TodoList } from '../stores/list.store'

defineProps<{
  list: TodoList
  isActive: boolean
}>()

defineEmits<{
  select: []
  edit: []
  delete: []
}>()
</script>

<template>
  <div
    class="list-item"
    :class="{ 'list-item--active': isActive }"
    role="button"
    tabindex="0"
    @click="$emit('select')"
    @keydown.enter="$emit('select')"
  >
    <span class="list-color" :style="{ backgroundColor: list.color }"></span>
    <span class="list-name">{{ list.name }}</span>
    <span v-if="list.todoCount > 0" class="list-count">{{ list.todoCount }}</span>
    <div class="list-actions">
      <button class="action-btn" title="重命名" @click.stop="$emit('edit')">
        &#9998;
      </button>
      <button class="action-btn action-btn--danger" title="删除" @click.stop="$emit('delete')">
        &times;
      </button>
    </div>
  </div>
</template>

<style scoped>
.list-item {
  display: flex;
  align-items: center;
  height: var(--size-clickable);
  padding: 0 var(--spacing-base);
  cursor: pointer;
  border-radius: var(--radius-sm);
  transition: background-color var(--duration-fast) var(--ease-out);
  position: relative;
}

.list-item:hover {
  background: var(--color-bg-hover);
}

.list-item--active {
  background: var(--color-brand-primary-light);
}

.list-item--active .list-name {
  color: var(--color-brand-primary);
  font-weight: var(--font-weight-medium);
}

.list-color {
  width: 8px;
  height: 8px;
  border-radius: var(--radius-full);
  flex-shrink: 0;
}

.list-name {
  flex: 1;
  margin-left: var(--spacing-sm);
  font-size: var(--font-size-base);
  color: var(--color-text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.list-count {
  font-size: var(--font-size-sm);
  color: var(--color-text-tertiary);
  background: var(--color-bg-hover);
  border-radius: var(--radius-full);
  padding: 2px var(--spacing-sm);
  min-width: 20px;
  text-align: center;
}

.list-actions {
  display: none;
  gap: var(--spacing-xs);
  margin-left: var(--spacing-xs);
}

.list-item:hover .list-actions {
  display: flex;
}

.action-btn {
  width: 28px;
  height: 28px;
  border: none;
  background: none;
  color: var(--color-text-tertiary);
  font-size: var(--font-size-sm);
  cursor: pointer;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color var(--duration-fast) var(--ease-out),
              background-color var(--duration-fast) var(--ease-out);
}

.action-btn:hover {
  color: var(--color-text-primary);
  background: var(--color-bg-hover);
}

.action-btn--danger:hover {
  color: var(--color-danger);
}
</style>
