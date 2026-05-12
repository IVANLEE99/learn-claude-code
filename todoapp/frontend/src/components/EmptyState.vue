<script setup lang="ts">
defineProps<{
  icon?: string
  title: string
  subtitle?: string
}>()
</script>

<template>
  <div class="empty-state">
    <div v-if="icon" class="empty-icon">{{ icon }}</div>
    <h3 class="empty-title">{{ title }}</h3>
    <p v-if="subtitle" class="empty-subtitle">{{ subtitle }}</p>
  </div>
</template>

<style scoped>
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-3xl) var(--spacing-xl);
  text-align: center;
}

.empty-icon {
  font-size: 64px;
  color: var(--color-text-tertiary);
  margin-bottom: var(--spacing-lg);
}

.empty-title {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-sm);
}

.empty-subtitle {
  font-size: var(--font-size-base);
  color: var(--color-text-tertiary);
}
</style>
