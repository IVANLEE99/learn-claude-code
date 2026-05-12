// 列表服务

import prisma from '../config/prisma'
import { ApiError } from '../utils/ApiError'


export async function getLists(userId: string) {
  const lists = await prisma.todoList.findMany({
    where: { userId },
    orderBy: { position: 'asc' },
    include: {
      _count: {
        select: {
          todos: {
            where: { completed: false },
          },
        },
      },
    },
  })

  return lists.map((list) => ({
    id: list.id,
    name: list.name,
    color: list.color,
    position: list.position,
    todoCount: list._count.todos,
    createdAt: list.createdAt.toISOString(),
    updatedAt: list.updatedAt.toISOString(),
  }))
}

export async function createList(userId: string, name: string, color: string) {
  // 获取当前用户已有列表数量作为新列表的 position
  const count = await prisma.todoList.count({ where: { userId } })

  const list = await prisma.todoList.create({
    data: {
      userId,
      name,
      color,
      position: count,
    },
  })

  return {
    id: list.id,
    name: list.name,
    color: list.color,
    position: list.position,
    todoCount: 0,
    createdAt: list.createdAt.toISOString(),
    updatedAt: list.updatedAt.toISOString(),
  }
}

export async function updateList(userId: string, listId: string, data: { name?: string; color?: string }) {
  // 检查列表是否存在且属于当前用户
  const list = await prisma.todoList.findUnique({ where: { id: listId } })
  if (!list) {
    throw new ApiError(404, 'LIST_NOT_FOUND', '列表不存在')
  }
  if (list.userId !== userId) {
    throw new ApiError(403, 'LIST_FORBIDDEN', '无权操作此列表')
  }

  const updated = await prisma.todoList.update({
    where: { id: listId },
    data,
    include: {
      _count: {
        select: {
          todos: {
            where: { completed: false },
          },
        },
      },
    },
  })

  return {
    id: updated.id,
    name: updated.name,
    color: updated.color,
    position: updated.position,
    todoCount: updated._count.todos,
    createdAt: updated.createdAt.toISOString(),
    updatedAt: updated.updatedAt.toISOString(),
  }
}

export async function deleteList(userId: string, listId: string) {
  const list = await prisma.todoList.findUnique({ where: { id: listId } })
  if (!list) {
    throw new ApiError(404, 'LIST_NOT_FOUND', '列表不存在')
  }
  if (list.userId !== userId) {
    throw new ApiError(403, 'LIST_FORBIDDEN', '无权操作此列表')
  }

  // 级联删除由 Prisma schema 的 onDelete: Cascade 处理
  await prisma.todoList.delete({ where: { id: listId } })

  return { message: '列表已删除' }
}
