<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth.store'

const router = useRouter()
const authStore = useAuthStore()

const nickname = ref('')
const oldPassword = ref('')
const newPassword = ref('')
const nicknameSuccess = ref('')
const nicknameError = ref('')
const passwordSuccess = ref('')
const passwordError = ref('')

onMounted(async () => {
  try {
    await authStore.fetchUser()
    nickname.value = authStore.user?.nickname || ''
  } catch {
    // 获取失败时跳转登录
    router.push({ name: 'login' })
  }
})

async function handleUpdateNickname() {
  nicknameSuccess.value = ''
  nicknameError.value = ''
  try {
    await authStore.updateNickname(nickname.value)
    nicknameSuccess.value = '昵称修改成功'
  } catch (err: any) {
    const errData = err.response?.data?.error
    nicknameError.value = errData?.message || '修改失败'
  }
}

async function handleChangePassword() {
  passwordSuccess.value = ''
  passwordError.value = ''
  try {
    await authStore.changePassword(oldPassword.value, newPassword.value)
    oldPassword.value = ''
    newPassword.value = ''
    passwordSuccess.value = '密码修改成功'
  } catch (err: any) {
    const errData = err.response?.data?.error
    passwordError.value = errData?.message || '修改失败'
  }
}

function handleLogout() {
  authStore.logout()
  router.push({ name: 'login' })
}
</script>

<template>
  <div class="settings-page">
    <header class="settings-header">
      <button class="btn-back" @click="router.push({ name: 'home' })">
        &larr; 返回
      </button>
      <h1 class="settings-title">个人设置</h1>
      <div class="header-spacer"></div>
    </header>

    <div class="settings-content">
      <section class="settings-section">
        <h2 class="section-title">基本信息</h2>
        <div class="info-row">
          <span class="info-label">邮箱</span>
          <span class="info-value">{{ authStore.user?.email }}</span>
        </div>
        <div class="info-row">
          <span class="info-label">注册时间</span>
          <span class="info-value">{{ authStore.user?.createdAt ? new Date(authStore.user.createdAt).toLocaleDateString('zh-CN') : '' }}</span>
        </div>
      </section>

      <section class="settings-section">
        <h2 class="section-title">修改昵称</h2>
        <form @submit.prevent="handleUpdateNickname">
          <div class="form-group">
            <label class="form-label" for="nickname">昵称</label>
            <input id="nickname" v-model="nickname" type="text" class="form-input" required />
          </div>
          <div v-if="nicknameSuccess" class="form-success">{{ nicknameSuccess }}</div>
          <div v-if="nicknameError" class="form-error">{{ nicknameError }}</div>
          <button type="submit" class="btn btn-primary">保存</button>
        </form>
      </section>

      <section class="settings-section">
        <h2 class="section-title">修改密码</h2>
        <form @submit.prevent="handleChangePassword">
          <div class="form-group">
            <label class="form-label" for="oldPassword">旧密码</label>
            <input id="oldPassword" v-model="oldPassword" type="password" class="form-input" required />
          </div>
          <div class="form-group">
            <label class="form-label" for="newPassword">新密码</label>
            <input id="newPassword" v-model="newPassword" type="password" class="form-input" required minlength="6" />
          </div>
          <div v-if="passwordSuccess" class="form-success">{{ passwordSuccess }}</div>
          <div v-if="passwordError" class="form-error">{{ passwordError }}</div>
          <button type="submit" class="btn btn-primary">修改密码</button>
        </form>
      </section>

      <section class="settings-section">
        <button class="btn btn-danger" @click="handleLogout">退出登录</button>
      </section>
    </div>
  </div>
</template>

<style scoped>
.settings-page {
  min-height: 100vh;
  background: var(--color-bg-page);
}

.settings-header {
  height: var(--size-header);
  background: var(--color-bg-card);
  border-bottom: 1px solid var(--color-border-light);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--spacing-base);
  position: sticky;
  top: 0;
  z-index: var(--z-sticky);
  padding-top: env(safe-area-inset-top);
}

.settings-title {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
}

.btn-back {
  background: none;
  border: none;
  color: var(--color-brand-primary);
  font-size: var(--font-size-base);
  font-family: var(--font-family);
  cursor: pointer;
  min-width: var(--size-clickable);
  min-height: var(--size-clickable);
  display: flex;
  align-items: center;
}

.header-spacer {
  width: var(--size-clickable);
}

.settings-content {
  max-width: 600px;
  margin: 0 auto;
  padding: var(--spacing-xl);
  padding-bottom: calc(var(--spacing-xl) + env(safe-area-inset-bottom));
}

.settings-section {
  background: var(--color-bg-card);
  border-radius: var(--radius-md);
  padding: var(--spacing-lg);
  margin-bottom: var(--spacing-base);
  box-shadow: var(--shadow-sm);
}

.section-title {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-base);
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-sm) 0;
  border-bottom: 1px solid var(--color-border-light);
}

.info-row:last-child {
  border-bottom: none;
}

.info-label {
  font-size: var(--font-size-base);
  color: var(--color-text-secondary);
}

.info-value {
  font-size: var(--font-size-base);
  color: var(--color-text-primary);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
  margin-bottom: var(--spacing-lg);
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

.form-success {
  font-size: var(--font-size-sm);
  color: var(--color-success);
  padding: var(--spacing-sm) var(--spacing-base);
  background: var(--color-success-light);
  border-radius: var(--radius-sm);
  margin-bottom: var(--spacing-md);
}

.form-error {
  font-size: var(--font-size-sm);
  color: var(--color-danger);
  padding: var(--spacing-sm) var(--spacing-base);
  background: var(--color-danger-light);
  border-radius: var(--radius-sm);
  margin-bottom: var(--spacing-md);
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
  width: 100%;
}

.btn-primary {
  background: var(--color-brand-primary);
  color: var(--color-text-inverse);
}

.btn-primary:hover {
  background: var(--color-brand-primary-dark);
}

.btn-primary:focus-visible {
  box-shadow: var(--shadow-focus);
}

.btn-danger {
  background: var(--color-danger);
  color: var(--color-text-inverse);
}

.btn-danger:hover {
  opacity: 0.9;
}
</style>
