// 数据库初始种子脚本
// MVP 阶段无需预置数据，用户注册后系统不自动创建列表

import { PrismaClient } from '@prisma/client'

const prisma = new PrismaClient()

async function main() {
  console.log('种子脚本执行完成（MVP 无预置数据）')
}

main()
  .catch((e) => {
    console.error(e)
    process.exit(1)
  })
  .finally(async () => {
    await prisma.$disconnect()
  })
