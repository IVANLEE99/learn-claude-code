// 待办服务

import prisma from '../config/prisma'
import { ApiError } from '../utils/ApiError'


const PRIORITY_ORDER: Record<string, number> = {
  high: 3,
  medium: 2,
  low: 1,
}

interface TodoQueryParams {
  listId?: string
  status?: string
  keyword?: string
}

interface UpdateTodoData {
  title?: string
  description?: string | null
  priority?: string
  listId?: string
}

export async function getTodos(userId: string, params: TodoQueryParams) {
  const where: any = { userId }

  if (params.listId) {
    where.listId = params.listId
  }

  if (params.status === 'active') {
    where.completed = false
  } else if (params.status === 'completed') {
    where.completed = true
  }

  if (params.keyword) {
    where.title = { contains: params.keyword, mode: 'insensitive' }
  }

  const todos = await prisma.todo.findMany({
    where,
    include: {
      list: {
        select: { name: true, color: true },
      },
    },
  })

  // 按 priority 降序，同优先级按 position 升序
  const sorted = todos.sort((a, b) => {
    const pa = PRIORITY_ORDER[a.priority] || 0
    const pb = PRIORITY_ORDER[b.priority] || 0
    if (pb !== pa) return pb - pa
    return a.position - b.position
  })

  return sorted.map((todo) => ({
    id: todo.id,
    title: todo.title,
    description: todo.description,
    priority: todo.priority,
    completed: todo.completed,
    listId: todo.listId,
    listName: todo.list.name,
    listColor: todo.list.color,
    position: todo.position,
    createdAt: todo.createdAt.toISOString(),
    updatedAt: todo.updatedAt.toISOString(),
  }))
}

export async function createTodo(
  userId: string,
  data: { title: string; description?: string; listId: string; priority?: string }
) {
  // 检查列表是否存在且属于当前用户
  const list = await prisma.todoList.findUnique({ where: { id: data.listId } })
  if (!list) {
    throw new ApiError(404, 'LIST_NOT_FOUND', '列表不存在')
  }
  if (list.userId !== userId) {
    throw new ApiError(403, 'LIST_FORBIDDEN', '无权在此列表创建待办')
  }

  // 获取该列表下已有待办数量作为 position
  const count = await prisma.todo.count({ where: { listId: data.listId } })

  const todo = await prisma.todo.create({
    data: {
      userId,
      listId: data.listId,
      title: data.title,
      description: data.description || null,
      priority: data.priority || 'medium',
      position: count,
    },
    include: {
      list: {
        select: { name: true, color: true },
      },
    },
  })

  return {
    id: todo.id,
    title: todo.title,
    description: todo.description,
    priority: todo.priority,
    completed: todo.completed,
    listId: todo.listId,
    listName: todo.list.name,
    listColor: todo.list.color,
    position: todo.position,
    createdAt: todo.createdAt.toISOString(),
    updatedAt: todo.updatedAt.toISOString(),
  }
}

export async function updateTodo(
  userId: string,
  todoId: string,
  data: UpdateTodoData
) {
  const todo = await prisma.todo.findUnique({ where: { id: todoId } })
  if (!todo) {
    throw new ApiError(404, 'TODO_NOT_FOUND', '待办不存在')
  }
  if (todo.userId !== userId) {
    throw new ApiError(403, 'TODO_FORBIDDEN', '无权操作此待办')
  }

  // 如果移动到新列表，检查新列表
  if (data.listId && data.listId !== todo.listId) {
    const list = await prisma.todoList.findUnique({ where: { id: data.listId } })
    if (!list) {
      throw new ApiError(404, 'LIST_NOT_FOUND', '目标列表不存在')
    }
    if (list.userId !== userId) {
      throw new ApiError(403, 'LIST_FORBIDDEN', '无权访问目标列表')
    }
  }

  const updateData: any = {}
  if (data.title !== undefined) updateData.title = data.title
  if (data.description !== undefined) updateData.description = data.description
  if (data.priority !== undefined) updateData.priority = data.priority
  if (data.listId !== undefined) updateData.listId = data.listId

  const updated = await prisma.todo.update({
    where: { id: todoId },
    data: updateData,
    include: {
      list: {
        select: { name: true, color: true },
      },
    },
  })

  return {
    id: updated.id,
    title: updated.title,
    description: updated.description,
    priority: updated.priority,
    completed: updated.completed,
    listId: updated.listId,
    listName: updated.list.name,
    listColor: updated.list.color,
    position: updated.position,
    createdAt: updated.createdAt.toISOString(),
    updatedAt: updated.updatedAt.toISOString(),
  }
}

export async function toggleTodo(userId: string, todoId: string) {
  const todo = await prisma.todo.findUnique({ where: { id: todoId } })
  if (!todo) {
    throw new ApiError(404, 'TODO_NOT_FOUND', '待办不存在')
  }
  if (todo.userId !== userId) {
    throw new ApiError(403, 'TODO_FORBIDDEN', '无权操作此待办')
  }

  const updated = await prisma.todo.update({
    where: { id: todoId },
    data: { completed: !todo.completed },
    include: {
      list: {
        select: { name: true, color: true },
      },
    },
  })

  return {
    id: updated.id,
    title: updated.title,
    description: updated.description,
    priority: updated.priority,
    completed: updated.completed,
    listId: updated.listId,
    listName: updated.list.name,
    listColor: updated.list.color,
    position: updated.position,
    createdAt: updated.createdAt.toISOString(),
    updatedAt: updated.updatedAt.toISOString(),
  }
}

export async function deleteTodo(userId: string, todoId: string) {
  const todo = await prisma.todo.findUnique({ where: { id: todoId } })
  if (!todo) {
    throw new ApiError(404, 'TODO_NOT_FOUND', '待办不存在')
  }
  if (todo.userId !== userId) {
    throw new ApiError(403, 'TODO_FORBIDDEN', '无权操作此待办')
  }

  await prisma.todo.delete({ where: { id: todoId } })

  return { message: '待办已删除' }
}
