// 用户服务

import prisma from '../config/prisma'
import bcrypt from 'bcryptjs'
import { ApiError } from '../utils/ApiError'


export async function getUserById(userId: string) {
  const user = await prisma.user.findUnique({
    where: { id: userId },
    select: {
      id: true,
      email: true,
      nickname: true,
      createdAt: true,
    },
  })

  if (!user) {
    throw new ApiError(401, 'AUTH_TOKEN_INVALID', '认证令牌无效')
  }

  return {
    id: user.id,
    email: user.email,
    nickname: user.nickname,
    createdAt: user.createdAt.toISOString(),
  }
}

export async function updateNickname(userId: string, nickname: string) {
  const user = await prisma.user.update({
    where: { id: userId },
    data: { nickname },
    select: {
      id: true,
      email: true,
      nickname: true,
      createdAt: true,
    },
  })

  return {
    id: user.id,
    email: user.email,
    nickname: user.nickname,
    createdAt: user.createdAt.toISOString(),
  }
}

export async function changePassword(userId: string, oldPassword: string, newPassword: string) {
  const user = await prisma.user.findUnique({ where: { id: userId } })
  if (!user) {
    throw new ApiError(401, 'AUTH_TOKEN_INVALID', '认证令牌无效')
  }

  const valid = await bcrypt.compare(oldPassword, user.passwordHash)
  if (!valid) {
    throw new ApiError(401, 'AUTH_OLD_PASSWORD_WRONG', '旧密码错误')
  }

  const newPasswordHash = await bcrypt.hash(newPassword, 10)
  await prisma.user.update({
    where: { id: userId },
    data: { passwordHash: newPasswordHash },
  })

  return { message: '密码修改成功' }
}
