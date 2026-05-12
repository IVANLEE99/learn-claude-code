<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth.store'
import { useListStore } from '../stores/list.store'
import { useTodoStore } from '../stores/todo.store'
import ListNav from '../components/ListNav.vue'
import FilterBar from '../components/FilterBar.vue'
import TodoCard from '../components/TodoCard.vue'
import TodoForm from '../components/TodoForm.vue'
import EmptyState from '../components/EmptyState.vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const listStore = useListStore()
const todoStore = useTodoStore()

const searchKeyword = ref('')
const showSidebar = ref(false)
const editingTodoId = ref<string | null>(null)
const editTitle = ref('')

// 初始化 URL query 中的 status
if (route.query.status && ['all', 'active', 'completed'].includes(route.query.status as string)) {
  todoStore.setFilterStatus(route.query.status as string)
}

onMounted(async () => {
  await listStore.fetchLists()
  await fetchTodos()
})

// 监听筛选和列表变化，重新获取待办
watch([() => todoStore.filterStatus, () => listStore.activeListId, searchKeyword], () => {
  fetchTodos()
})

async function fetchTodos() {
  try {
    await todoStore.fetchTodos({
      listId: listStore.activeListId || undefined,
      status: todoStore.filterStatus === 'all' ? undefined : todoStore.filterStatus,
      keyword: searchKeyword.value || undefined,
    })
  } catch {
    // 错误由 axios 拦截器处理
  }
}

const filteredTodos = computed(() => todoStore.todos)

async function handleToggle(id: string) {
  try {
    await todoStore.toggleTodo(id)
    // 更新列表的 todoCount
    await listStore.fetchLists()
  } catch {
    // 错误由 axios 拦截器处理
  }
}

async function handleDelete(id: string) {
  if (!confirm('确定删除此待办吗？')) return
  try {
    await todoStore.deleteTodo(id)
    await listStore.fetchLists()
  } catch {
    // 错误由 axios 拦截器处理
  }
}

function startEdit(id: string, currentTitle: string) {
  editingTodoId.value = id
  editTitle.value = currentTitle
}

async function handleEditSave(id: string) {
  if (!editTitle.value.trim()) {
    editingTodoId.value = null
    return
  }
  try {
    await todoStore.updateTodo(id, { title: editTitle.value.trim() })
    editingTodoId.value = null
  } catch {
    // 错误由 axios 拦截器处理
  }
}

function handleEditCancel() {
  editingTodoId.value = null
}

function toggleSidebar() {
  showSidebar.value = !showSidebar.value
}
</script>

<template>
  <div class="home-page">
    <!-- 移动端遮罩 -->
    <div
      v-if="showSidebar"
      class="sidebar-overlay"
      @click="showSidebar = false"
    ></div>

    <!-- 侧边栏 -->
    <aside
      class="sidebar"
      :class="{ 'sidebar--open': showSidebar }"
    >
      <ListNav />
      <div class="sidebar-footer">
        <router-link to="/settings" class="settings-link">
          {{ authStore.user?.nickname || '设置' }}
        </router-link>
      </div>
    </aside>

    <!-- 主内容区 -->
    <main class="main-content">
      <header class="main-header">
        <button class="menu-btn" @click="toggleSidebar">
          &#9776;
        </button>
        <h1 class="main-title">待办事项</h1>
        <router-link to="/settings" class="settings-btn">
          {{ authStore.user?.nickname?.charAt(0) || '?' }}
        </router-link>
      </header>

      <!-- 搜索框 -->
      <div class="search-bar">
        <input
          v-model="searchKeyword"
          class="search-input"
          placeholder="搜索待办..."
          type="search"
        />
      </div>

      <!-- 筛选栏 -->
      <FilterBar />

      <!-- 新建待办表单 -->
      <TodoForm />

      <!-- 待办列表 -->
      <div v-if="filteredTodos.length > 0" class="todo-list" role="list">
        <div v-for="todo in filteredTodos" :key="todo.id">
          <!-- 编辑模式 -->
          <div v-if="editingTodoId === todo.id" class="edit-item">
            <input
              v-model="editTitle"
              class="edit-input"
              @keyup.enter="handleEditSave(todo.id)"
              @keyup.escape="handleEditCancel"
            />
            <button class="btn-save" @click="handleEditSave(todo.id)">保存</button>
            <button class="btn-cancel" @click="handleEditCancel">取消</button>
          </div>
          <!-- 正常模式 -->
          <TodoCard
            v-else
            :todo="todo"
            @toggle="handleToggle(todo.id)"
            @delete="handleDelete(todo.id)"
            @edit="startEdit(todo.id, todo.title)"
          />
        </div>
      </div>

      <!-- 空状态 -->
      <EmptyState
        v-else
        icon="&#128203;"
        title="暂无待办"
        subtitle="点击上方表单添加第一条待办吧"
      />
    </main>
  </div>
</template>

<style scoped>
.home-page {
  display: flex;
  min-height: 100vh;
}

/* ---- 侧边栏 ---- */
.sidebar-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: var(--z-overlay);
}

.sidebar {
  width: var(--size-sidebar);
  background: var(--color-bg-card);
  border-right: 1px solid var(--color-border-light);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  z-index: var(--z-drawer);
  transform: translateX(-100%);
  transition: transform var(--duration-normal) var(--ease-out);
}

.sidebar--open {
  transform: translateX(0);
}

.sidebar-footer {
  padding: var(--spacing-base);
  border-top: 1px solid var(--color-border-light);
}

.settings-link {
  color: var(--color-text-secondary);
  text-decoration: none;
  font-size: var(--font-size-sm);
  display: flex;
  align-items: center;
  min-height: var(--size-clickable);
}

.settings-link:hover {
  color: var(--color-brand-primary);
}

/* ---- 桌面端侧边栏常驻 ---- */
@media (min-width: 768px) {
  .sidebar {
    position: static;
    transform: none;
  }

  .sidebar-overlay {
    display: none;
  }

  .menu-btn {
    display: none;
  }
}

/* ---- 主内容区 ---- */
.main-content {
  flex: 1;
  min-width: 0;
  background: var(--color-bg-page);
  display: flex;
  flex-direction: column;
}

.main-header {
  height: var(--size-header);
  background: var(--color-bg-card);
  border-bottom: 1px solid var(--color-border-light);
  display: flex;
  align-items: center;
  padding: 0 var(--spacing-base);
  gap: var(--spacing-base);
  position: sticky;
  top: 0;
  z-index: var(--z-sticky);
  padding-top: env(safe-area-inset-top);
}

.menu-btn {
  width: var(--size-clickable);
  height: var(--size-clickable);
  border: none;
  background: none;
  font-size: var(--font-size-lg);
  color: var(--color-text-primary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.main-title {
  flex: 1;
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
}

.settings-btn {
  width: var(--size-avatar);
  height: var(--size-avatar);
  border-radius: var(--radius-full);
  background: var(--color-brand-primary);
  color: var(--color-text-inverse);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  text-decoration: none;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* ---- 搜索框 ---- */
.search-bar {
  padding: var(--spacing-base);
}

.search-input {
  width: 100%;
  height: 40px;
  padding: 0 var(--spacing-base);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-bg-card);
  color: var(--color-text-primary);
  font-size: var(--font-size-base);
  font-family: var(--font-family);
}

.search-input:focus {
  outline: none;
  border-color: var(--color-brand-primary);
  box-shadow: var(--shadow-focus);
}

.search-input::placeholder {
  color: var(--color-text-tertiary);
}

/* ---- 待办列表 ---- */
.todo-list {
  padding: 0 var(--spacing-base);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
  padding-bottom: calc(var(--spacing-xl) + env(safe-area-inset-bottom));
}

/* ---- 编辑项 ---- */
.edit-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  background: var(--color-bg-card);
  border-radius: var(--radius-md);
  padding: var(--spacing-base);
  box-shadow: var(--shadow-sm);
}

.edit-input {
  flex: 1;
  height: 36px;
  padding: 0 var(--spacing-base);
  border: 1px solid var(--color-brand-primary);
  border-radius: var(--radius-md);
  background: var(--color-bg-card);
  color: var(--color-text-primary);
  font-size: var(--font-size-base);
  font-family: var(--font-family);
  box-shadow: var(--shadow-focus);
}

.edit-input:focus {
  outline: none;
}

.btn-save,
.btn-cancel {
  height: 36px;
  padding: 0 var(--spacing-base);
  border: none;
  border-radius: var(--radius-sm);
  font-size: var(--font-size-sm);
  font-family: var(--font-family);
  cursor: pointer;
}

.btn-save {
  background: var(--color-brand-primary);
  color: var(--color-text-inverse);
}

.btn-cancel {
  background: var(--color-bg-hover);
  color: var(--color-text-secondary);
}
</style>
