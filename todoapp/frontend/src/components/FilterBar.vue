<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'
import { useTodoStore } from '../stores/todo.store'

const route = useRoute()
const router = useRouter()
const todoStore = useTodoStore()

const filters = [
  { key: 'all', label: '全部' },
  { key: 'active', label: '未完成' },
  { key: 'completed', label: '已完成' },
]

function setFilter(key: string) {
  todoStore.setFilterStatus(key)
  router.replace({ query: { ...route.query, status: key === 'all' ? undefined : key } })
}
</script>

<template>
  <div class="filter-bar">
    <button
      v-for="f in filters"
      :key="f.key"
      class="filter-item"
      :class="{ 'filter-item--active': todoStore.filterStatus === f.key }"
      @click="setFilter(f.key)"
    >
      {{ f.label }}
    </button>
  </div>
</template>

<style scoped>
.filter-bar {
  display: flex;
  gap: var(--spacing-md);
  height: 40px;
  align-items: center;
  padding: 0 var(--spacing-base);
  border-bottom: 1px solid var(--color-border-light);
}

.filter-item {
  background: none;
  border: none;
  font-size: var(--font-size-sm);
  font-family: var(--font-family);
  color: var(--color-text-secondary);
  cursor: pointer;
  padding: var(--spacing-xs) var(--spacing-sm);
  position: relative;
  transition: color var(--duration-fast) var(--ease-out);
  min-height: var(--size-clickable);
  display: flex;
  align-items: center;
}

.filter-item--active {
  color: var(--color-brand-primary);
  font-weight: var(--font-weight-medium);
}

.filter-item--active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: var(--color-brand-primary);
  border-radius: 1px;
}

.filter-item:hover {
  color: var(--color-brand-primary);
}
</style>
