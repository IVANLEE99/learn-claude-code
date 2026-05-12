// 统一错误处理中间件

import { Request, Response, NextFunction } from 'express'
import { ApiError } from '../utils/ApiError'

export function errorHandler(err: Error, _req: Request, res: Response, _next: NextFunction): void {
  if (err instanceof ApiError) {
    res.status(err.statusCode).json({
      success: false,
      error: {
        code: err.code,
        message: err.message,
      },
    })
    return
  }

  // Zod 校验错误
  if (err.name === 'ZodError') {
    res.status(400).json({
      success: false,
      error: {
        code: 'VALIDATION_FAILED',
        message: '请求参数校验失败',
      },
    })
    return
  }

  console.error('未处理的错误：', err)
  res.status(500).json({
    success: false,
    error: {
      code: 'SERVER_INTERNAL_ERROR',
      message: '服务器内部错误',
    },
  })
}
