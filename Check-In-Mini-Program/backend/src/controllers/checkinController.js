const checkinService = require('../services/checkinService')
const { success, error } = require('../utils/response')

/**
 * POST /api/v1/checkin
 * 每日打卡签到
 */
async function checkin(ctx) {
  const userId = ctx.state.userId

  // 检查今日是否已打卡
  const alreadyChecked = await checkinService.hasCheckedInToday(userId)
  if (alreadyChecked) {
    return error(ctx, 409, 'already_checked_in', '今日已打卡')
  }

  // 创建打卡记录
  const checkinRecord = await checkinService.createCheckin(userId)

  // 计算连续打卡天数
  const consecutiveDays = await checkinService.getConsecutiveDays(userId)
  const maxConsecutiveDays = await checkinService.getMaxConsecutiveDays(userId)

  return success(ctx, {
    checkinId: Number(checkinRecord.id),
    checkinDate: checkinService.formatDate(checkinRecord.checkinDate),
    consecutiveDays,
    maxConsecutiveDays
  })
}

/**
 * GET /api/v1/checkin/status
 * 获取今日打卡状态
 */
async function getStatus(ctx) {
  const userId = ctx.state.userId

  const isCheckedIn = await checkinService.hasCheckedInToday(userId)
  const consecutiveDays = await checkinService.getConsecutiveDays(userId)
  const maxConsecutiveDays = await checkinService.getMaxConsecutiveDays(userId)
  const today = checkinService.getTodayDate()

  return success(ctx, {
    isCheckedIn,
    checkinDate: checkinService.formatDate(today),
    consecutiveDays,
    maxConsecutiveDays
  })
}

/**
 * GET /api/v1/checkin/history
 * 获取打卡历史记录
 */
async function getHistory(ctx) {
  const userId = ctx.state.userId
  const now = new Date()

  const year = parseInt(ctx.query.year) || now.getFullYear()
  const month = parseInt(ctx.query.month) || now.getMonth() + 1
  const page = parseInt(ctx.query.page) || 1
  const pageSize = parseInt(ctx.query.pageSize) || 31

  const result = await checkinService.getHistory(userId, year, month, page, pageSize)

  return success(ctx, result)
}

module.exports = { checkin, getStatus, getHistory }
