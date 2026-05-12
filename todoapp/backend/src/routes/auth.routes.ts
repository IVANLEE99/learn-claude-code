// 认证路由

import { Router, Request, Response, NextFunction } from 'express'
import { z } from 'zod'
import * as authService from '../services/auth.service'
import { ApiError } from '../utils/ApiError'

const router = Router()

const registerSchema = z.object({
  email: z.string().email('邮箱格式错误'),
  password: z.string().min(6, '密码最少 6 位'),
  nickname: z.string().min(1, '昵称不能为空').max(50, '昵称最多 50 字符'),
})

const loginSchema = z.object({
  email: z.string().min(1, '邮箱不能为空'),
  password: z.string().min(1, '密码不能为空'),
})

// POST /api/v1/auth/register
router.post('/register', async (req: Request, res: Response, next: NextFunction) => {
  try {
    const parsed = registerSchema.safeParse(req.body)
    if (!parsed.success) {
      throw new ApiError(400, 'VALIDATION_FAILED', '请求参数校验失败')
    }

    const result = await authService.register(parsed.data.email, parsed.data.password, parsed.data.nickname)
    res.status(201).json({ success: true, data: result })
  } catch (err) {
    next(err)
  }
})

// POST /api/v1/auth/login
router.post('/login', async (req: Request, res: Response, next: NextFunction) => {
  try {
    const parsed = loginSchema.safeParse(req.body)
    if (!parsed.success) {
      throw new ApiError(400, 'VALIDATION_FAILED', '请求参数校验失败')
    }

    const result = await authService.login(parsed.data.email, parsed.data.password)
    res.status(200).json({ success: true, data: result })
  } catch (err) {
    next(err)
  }
})

export default router
