const { PrismaClient } = require('@prisma/client')
const prisma = new PrismaClient()

/**
 * 获取今日日期（UTC，只取日期部分）
 */
function getTodayDate() {
  const now = new Date()
  return new Date(now.getFullYear(), now.getMonth(), now.getDate())
}

/**
 * 创建打卡记录
 */
async function createCheckin(userId) {
  const today = getTodayDate()

  return prisma.checkin.create({
    data: {
      userId: BigInt(userId),
      checkinDate: today
    }
  })
}

/**
 * 检查今日是否已打卡
 */
async function hasCheckedInToday(userId) {
  const today = getTodayDate()

  const checkin = await prisma.checkin.findUnique({
    where: {
      userId_checkinDate: {
        userId: BigInt(userId),
        checkinDate: today
      }
    }
  })

  return !!checkin
}

/**
 * 计算连续打卡天数
 */
async function getConsecutiveDays(userId) {
  const today = getTodayDate()

  let consecutiveDays = 0
  let checkDate = new Date(today)

  while (true) {
    const checkin = await prisma.checkin.findUnique({
      where: {
        userId_checkinDate: {
          userId: BigInt(userId),
          checkinDate: checkDate
        }
      }
    })

    if (!checkin) break

    consecutiveDays++
    checkDate.setDate(checkDate.getDate() - 1)
  }

  return consecutiveDays
}

/**
 * 获取历史最高连续打卡天数
 */
async function getMaxConsecutiveDays(userId) {
  const allCheckins = await prisma.checkin.findMany({
    where: { userId: BigInt(userId) },
    orderBy: { checkinDate: 'asc' },
    select: { checkinDate: true }
  })

  if (allCheckins.length === 0) return 0

  let maxDays = 1
  let currentDays = 1

  for (let i = 1; i < allCheckins.length; i++) {
    const prevDate = new Date(allCheckins[i - 1].checkinDate)
    const currDate = new Date(allCheckins[i].checkinDate)
    const diffDays = (currDate - prevDate) / (1000 * 60 * 60 * 24)

    if (diffDays === 1) {
      currentDays++
      maxDays = Math.max(maxDays, currentDays)
    } else {
      currentDays = 1
    }
  }

  return maxDays
}

/**
 * 获取打卡历史
 */
async function getHistory(userId, year, month, page, pageSize) {
  const startDate = new Date(year, month - 1, 1)
  const endDate = new Date(year, month, 0)

  const where = {
    userId: BigInt(userId),
    checkinDate: {
      gte: startDate,
      lte: endDate
    }
  }

  const [list, total] = await Promise.all([
    prisma.checkin.findMany({
      where,
      orderBy: { checkinDate: 'desc' },
      skip: (page - 1) * pageSize,
      take: pageSize,
      select: {
        id: true,
        checkinDate: true,
        createdAt: true
      }
    }),
    prisma.checkin.count({ where })
  ])

  return {
    list: list.map(item => ({
      id: Number(item.id),
      checkinDate: formatDate(item.checkinDate),
      createdAt: item.createdAt.toISOString()
    })),
    total,
    year,
    month
  }
}

/**
 * 获取总打卡天数
 */
async function getTotalCheckinDays(userId) {
  return prisma.checkin.count({
    where: { userId: BigInt(userId) }
  })
}

/**
 * 格式化日期为 YYYY-MM-DD
 */
function formatDate(date) {
  const d = new Date(date)
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

module.exports = {
  createCheckin,
  hasCheckedInToday,
  getConsecutiveDays,
  getMaxConsecutiveDays,
  getHistory,
  getTotalCheckinDays,
  getTodayDate,
  formatDate
}
