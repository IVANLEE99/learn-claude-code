// 列表路由

import { Router, Request, Response, NextFunction } from 'express'
import { z } from 'zod'
import { authMiddleware, AuthRequest } from '../middleware/auth'
import * as listService from '../services/list.service'
import { ApiError } from '../utils/ApiError'

const router = Router()

const createListSchema = z.object({
  name: z.string().min(1, '列表名称不能为空').max(100, '列表名称最多 100 字符'),
  color: z.string().regex(/^#[0-9A-Fa-f]{6}$/, '颜色格式错误，需为 #RRGGBB'),
})

const updateListSchema = z.object({
  name: z.string().min(1, '列表名称不能为空').max(100, '列表名称最多 100 字符').optional(),
  color: z.string().regex(/^#[0-9A-Fa-f]{6}$/, '颜色格式错误，需为 #RRGGBB').optional(),
}).refine(data => data.name !== undefined || data.color !== undefined, {
  message: '至少提供一个字段',
})

// GET /api/v1/lists
router.get('/', authMiddleware, async (req: AuthRequest, res: Response, next: NextFunction) => {
  try {
    const userId = req.userId!
    const lists = await listService.getLists(userId)
    res.status(200).json({ success: true, data: lists })
  } catch (err) {
    next(err)
  }
})

// POST /api/v1/lists
router.post('/', authMiddleware, async (req: AuthRequest, res: Response, next: NextFunction) => {
  try {
    const parsed = createListSchema.safeParse(req.body)
    if (!parsed.success) {
      throw new ApiError(400, 'VALIDATION_FAILED', '请求参数校验失败')
    }

    const userId = req.userId!
    const list = await listService.createList(userId, parsed.data.name, parsed.data.color)
    res.status(201).json({ success: true, data: list })
  } catch (err) {
    next(err)
  }
})

// PUT /api/v1/lists/:id
router.put('/:id', authMiddleware, async (req: AuthRequest, res: Response, next: NextFunction) => {
  try {
    const parsed = updateListSchema.safeParse(req.body)
    if (!parsed.success) {
      throw new ApiError(400, 'VALIDATION_FAILED', '请求参数校验失败')
    }

    const userId = req.userId!
    const list = await listService.updateList(userId, req.params.id, parsed.data)
    res.status(200).json({ success: true, data: list })
  } catch (err) {
    next(err)
  }
})

// DELETE /api/v1/lists/:id
router.delete('/:id', authMiddleware, async (req: AuthRequest, res: Response, next: NextFunction) => {
  try {
    const userId = req.userId!
    const result = await listService.deleteList(userId, req.params.id)
    res.status(200).json({ success: true, data: result })
  } catch (err) {
    next(err)
  }
})

export default router
