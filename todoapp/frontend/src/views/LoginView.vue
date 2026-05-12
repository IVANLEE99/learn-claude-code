<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth.store'

const router = useRouter()
const authStore = useAuthStore()

const email = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function handleSubmit() {
  error.value = ''
  loading.value = true
  try {
    await authStore.login(email.value, password.value)
    router.push({ name: 'home' })
  } catch (err: any) {
    const errData = err.response?.data?.error
    error.value = errData?.message || '登录失败，请稍后重试'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <div class="login-card">
      <h1 class="login-title">登录</h1>
      <form class="login-form" @submit.prevent="handleSubmit">
        <div class="form-group">
          <label class="form-label" for="email">邮箱</label>
          <input
            id="email"
            v-model="email"
            type="email"
            class="form-input"
            placeholder="请输入邮箱"
            required
          />
        </div>
        <div class="form-group">
          <label class="form-label" for="password">密码</label>
          <input
            id="password"
            v-model="password"
            type="password"
            class="form-input"
            placeholder="请输入密码"
            required
          />
        </div>
        <div v-if="error" class="form-error">{{ error }}</div>
        <button type="submit" class="btn btn-primary" :disabled="loading">
          {{ loading ? '登录中...' : '登录' }}
        </button>
      </form>
      <div class="login-footer">
        还没有账号？
        <router-link to="/register" class="link">去注册</router-link>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-xl);
  padding-top: env(safe-area-inset-top);
  padding-bottom: env(safe-area-inset-bottom);
}

.login-card {
  width: 100%;
  max-width: 400px;
  background: var(--color-bg-card);
  border-radius: var(--radius-lg);
  padding: var(--spacing-2xl);
  box-shadow: var(--shadow-md);
}

.login-title {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-bold);
  text-align: center;
  margin-bottom: var(--spacing-2xl);
  color: var(--color-text-primary);
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.form-label {
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
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
  transition: border-color var(--duration-fast) var(--ease-out),
              box-shadow var(--duration-fast) var(--ease-out);
}

.form-input:focus {
  outline: none;
  border-color: var(--color-brand-primary);
  box-shadow: var(--shadow-focus);
}

.form-input::placeholder {
  color: var(--color-text-tertiary);
}

.form-error {
  font-size: var(--font-size-sm);
  color: var(--color-danger);
  padding: var(--spacing-sm) var(--spacing-base);
  background: var(--color-danger-light);
  border-radius: var(--radius-sm);
}

.btn {
  height: var(--size-clickable);
  border: none;
  border-radius: var(--radius-sm);
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-medium);
  font-family: var(--font-family);
  cursor: pointer;
  transition: background-color var(--duration-fast) var(--ease-out);
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-primary {
  background: var(--color-brand-primary);
  color: var(--color-text-inverse);
}

.btn-primary:hover {
  background: var(--color-brand-primary-dark);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary:focus-visible {
  box-shadow: var(--shadow-focus);
}

.login-footer {
  text-align: center;
  margin-top: var(--spacing-xl);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.link {
  color: var(--color-brand-primary);
  text-decoration: none;
  font-weight: var(--font-weight-medium);
}

.link:hover {
  text-decoration: underline;
}
</style>
