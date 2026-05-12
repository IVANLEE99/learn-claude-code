// Prisma Client 单例
// 避免多个 service 文件各自实例化导致连接池耗尽

import { PrismaClient } from '@prisma/client'

const prisma = new PrismaClient()

export default prisma
