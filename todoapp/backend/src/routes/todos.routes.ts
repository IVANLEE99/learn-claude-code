// 待办路由

import { Router, Request, Response, NextFunction } from 'express'
import { z } from 'zod'
import { authMiddleware, AuthRequest } from '../middleware/auth'
import * as todoService from '../services/todo.service'
import { ApiError } from '../utils/ApiError'

const router = Router()

const createTodoSchema = z.object({
  title: z.string().min(1, '待办标题不能为空').max(255, '待办标题最多 255 字符'),
  description: z.string().max(2000, '描述最多 2000 字符').optional(),
  listId: z.string().min(1, '所属列表不能为空'),
  priority: z.enum(['high', 'medium', 'low']).optional(),
})

const updateTodoSchema = z.object({
  title: z.string().min(1, '待办标题不能为空').max(255, '待办标题最多 255 字符').optional(),
  description: z.string().max(2000, '描述最多 2000 字符').nullable().optional(),
  priority: z.enum(['high', 'medium', 'low']).optional(),
  listId: z.string().min(1, '所属列表不能为空').optional(),
}).refine(data => data.title !== undefined || data.description !== undefined || data.priority !== undefined || data.listId !== undefined, {
  message: '至少提供一个字段',
})

// GET /api/v1/todos
router.get('/', authMiddleware, async (req: AuthRequest, res: Response, next: NextFunction) => {
  try {
    const userId = req.userId!
    const { listId, status, keyword } = req.query

    // 校验 status 参数
    if (status && !['all', 'active', 'completed'].includes(status as string)) {
      throw new ApiError(400, 'VALIDATION_FAILED', '请求参数校验失败')
    }

    const todos = await todoService.getTodos(userId, {
      listId: listId as string | undefined,
      status: status as string | undefined,
      keyword: keyword as string | undefined,
    })
    res.status(200).json({ success: true, data: todos })
  } catch (err) {
    next(err)
  }
})

// POST /api/v1/todos
router.post('/', authMiddleware, async (req: AuthRequest, res: Response, next: NextFunction) => {
  try {
    const parsed = createTodoSchema.safeParse(req.body)
    if (!parsed.success) {
      throw new ApiError(400, 'VALIDATION_FAILED', '请求参数校验失败')
    }

    const userId = req.userId!
    const todo = await todoService.createTodo(userId, parsed.data)
    res.status(201).json({ success: true, data: todo })
  } catch (err) {
    next(err)
  }
})

// PUT /api/v1/todos/:id
router.put('/:id', authMiddleware, async (req: AuthRequest, res: Response, next: NextFunction) => {
  try {
    const parsed = updateTodoSchema.safeParse(req.body)
    if (!parsed.success) {
      throw new ApiError(400, 'VALIDATION_FAILED', '请求参数校验失败')
    }

    const userId = req.userId!
    const todo = await todoService.updateTodo(userId, req.params.id, parsed.data)
    res.status(200).json({ success: true, data: todo })
  } catch (err) {
    next(err)
  }
})

// PATCH /api/v1/todos/:id/toggle
router.patch('/:id/toggle', authMiddleware, async (req: AuthRequest, res: Response, next: NextFunction) => {
  try {
    const userId = req.userId!
    const todo = await todoService.toggleTodo(userId, req.params.id)
    res.status(200).json({ success: true, data: todo })
  } catch (err) {
    next(err)
  }
})

// DELETE /api/v1/todos/:id
router.delete('/:id', authMiddleware, async (req: AuthRequest, res: Response, next: NextFunction) => {
  try {
    const userId = req.userId!
    const result = await todoService.deleteTodo(userId, req.params.id)
    res.status(200).json({ success: true, data: result })
  } catch (err) {
    next(err)
  }
})

export default router
