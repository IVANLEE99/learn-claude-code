const authService = require('../services/authService')
const checkinService = require('../services/checkinService')
const { success, error } = require('../utils/response')

/**
 * GET /api/v1/users/me
 * 获取当前用户信息及统计数据
 */
async function getMe(ctx) {
  const userId = ctx.state.userId

  const user = await authService.findById(userId)
  if (!user) {
    return error(ctx, 404, 'not_found', '用户不存在')
  }

  const totalCheckinDays = await checkinService.getTotalCheckinDays(userId)
  const consecutiveDays = await checkinService.getConsecutiveDays(userId)
  const maxConsecutiveDays = await checkinService.getMaxConsecutiveDays(userId)

  return success(ctx, {
    id: Number(user.id),
    nickName: user.nickName,
    avatarUrl: user.avatarUrl,
    totalCheckinDays,
    consecutiveDays,
    maxConsecutiveDays,
    createdAt: user.createdAt.toISOString()
  })
}

module.exports = { getMe }
