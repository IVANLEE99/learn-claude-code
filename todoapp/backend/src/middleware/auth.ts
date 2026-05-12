// JWT 鉴权中间件

import { Request, Response, NextFunction } from 'express'
import jwt from 'jsonwebtoken'
import { ApiError } from '../utils/ApiError'
import { env } from '../config/env'

export interface AuthRequest extends Request {
  userId?: string
}

export function authMiddleware(req: AuthRequest, _res: Response, next: NextFunction): void {
  const authHeader = req.headers.authorization

  if (!authHeader) {
    throw new ApiError(401, 'AUTH_TOKEN_MISSING', '未提供认证令牌')
  }

  const parts = authHeader.split(' ')
  if (parts.length !== 2 || parts[0] !== 'Bearer') {
    throw new ApiError(401, 'AUTH_TOKEN_INVALID', '认证令牌无效')
  }

  const token = parts[1]

  try {
    const decoded = jwt.verify(token, env.JWT_SECRET) as { userId: string }
    req.userId = decoded.userId
    next()
  } catch (err: any) {
    if (err.name === 'TokenExpiredError') {
      throw new ApiError(401, 'AUTH_TOKEN_EXPIRED', '认证令牌已过期')
    }
    throw new ApiError(401, 'AUTH_TOKEN_INVALID', '认证令牌无效')
  }
}
