// 用户路由

import { Router, Request, Response, NextFunction } from 'express'
import { z } from 'zod'
import { authMiddleware, AuthRequest } from '../middleware/auth'
import * as userService from '../services/user.service'
import { ApiError } from '../utils/ApiError'

const router = Router()

const updateNicknameSchema = z.object({
  nickname: z.string().min(1, '昵称不能为空').max(50, '昵称最多 50 字符'),
})

const changePasswordSchema = z.object({
  oldPassword: z.string().min(1, '旧密码不能为空'),
  newPassword: z.string().min(6, '新密码最少 6 位'),
})

// GET /api/v1/users/me
router.get('/me', authMiddleware, async (req: AuthRequest, res: Response, next: NextFunction) => {
  try {
    const userId = req.userId!
    const user = await userService.getUserById(userId)
    res.status(200).json({ success: true, data: user })
  } catch (err) {
    next(err)
  }
})

// PUT /api/v1/users/me
router.put('/me', authMiddleware, async (req: AuthRequest, res: Response, next: NextFunction) => {
  try {
    const parsed = updateNicknameSchema.safeParse(req.body)
    if (!parsed.success) {
      throw new ApiError(400, 'VALIDATION_FAILED', '请求参数校验失败')
    }

    const userId = req.userId!
    const user = await userService.updateNickname(userId, parsed.data.nickname)
    res.status(200).json({ success: true, data: user })
  } catch (err) {
    next(err)
  }
})

// PUT /api/v1/users/me/password
router.put('/me/password', authMiddleware, async (req: AuthRequest, res: Response, next: NextFunction) => {
  try {
    const parsed = changePasswordSchema.safeParse(req.body)
    if (!parsed.success) {
      throw new ApiError(400, 'VALIDATION_FAILED', '请求参数校验失败')
    }

    const userId = req.userId!
    const result = await userService.changePassword(userId, parsed.data.oldPassword, parsed.data.newPassword)
    res.status(200).json({ success: true, data: result })
  } catch (err) {
    next(err)
  }
})

export default router
