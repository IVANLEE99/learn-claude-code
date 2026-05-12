// 认证服务

import prisma from '../config/prisma'
import bcrypt from 'bcryptjs'
import jwt from 'jsonwebtoken'
import { ApiError } from '../utils/ApiError'
import { env } from '../config/env'


export interface AuthResponse {
  user: {
    id: string
    email: string
    nickname: string
    createdAt: string
  }
  token: string
}

function generateToken(userId: string): string {
  return jwt.sign({ userId }, env.JWT_SECRET, { expiresIn: env.JWT_EXPIRES_IN as any })
}

function formatUserResponse(user: { id: string; email: string; nickname: string; createdAt: Date }): AuthResponse['user'] {
  return {
    id: user.id,
    email: user.email,
    nickname: user.nickname,
    createdAt: user.createdAt.toISOString(),
  }
}

export async function register(email: string, password: string, nickname: string): Promise<AuthResponse> {
  // 检查邮箱是否已存在
  const existing = await prisma.user.findUnique({ where: { email } })
  if (existing) {
    throw new ApiError(409, 'USER_EMAIL_EXISTS', '该邮箱已注册')
  }

  // 密码哈希
  const passwordHash = await bcrypt.hash(password, 10)

  // 创建用户
  const user = await prisma.user.create({
    data: {
      email,
      passwordHash,
      nickname,
    },
  })

  const token = generateToken(user.id)

  return {
    user: formatUserResponse(user),
    token,
  }
}

export async function login(email: string, password: string): Promise<AuthResponse> {
  // 查找用户
  const user = await prisma.user.findUnique({ where: { email } })
  if (!user) {
    throw new ApiError(401, 'AUTH_INVALID_CREDENTIALS', '邮箱或密码错误')
  }

  // 校验密码
  const valid = await bcrypt.compare(password, user.passwordHash)
  if (!valid) {
    throw new ApiError(401, 'AUTH_INVALID_CREDENTIALS', '邮箱或密码错误')
  }

  const token = generateToken(user.id)

  return {
    user: formatUserResponse(user),
    token,
  }
}
