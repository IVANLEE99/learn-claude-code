const { code2Session } = require('../services/wxService')
const authService = require('../services/authService')
const { generateToken } = require('../utils/jwt')
const { success, error } = require('../utils/response')

/**
 * POST /api/v1/auth/wx-login
 * 微信登录
 */
async function wxLogin(ctx) {
  const { code, userInfo } = ctx.request.body

  // 校验 code 参数
  if (!code) {
    return error(ctx, 400, 'missing_code', '缺少 code 参数')
  }

  try {
    // 1. 用 code 换取 openid
    const wxResult = await code2Session(code)

    // 2. 查找或创建用户
    let user = await authService.findByOpenid(wxResult.openid)
    let isNewUser = false

    if (!user) {
      user = await authService.create({
        openid: wxResult.openid,
        unionid: wxResult.unionid,
        nickName: userInfo?.nickName || '微信用户',
        avatarUrl: userInfo?.avatarUrl || ''
      })
      isNewUser = true
    } else if (userInfo) {
      // 更新用户信息
      await authService.update(user.id, {
        nickName: userInfo.nickName,
        avatarUrl: userInfo.avatarUrl
      })
      user = await authService.findById(user.id)
    }

    // 3. 生成 JWT（不返回 openid 和 session_key）
    const token = generateToken({ userId: Number(user.id) })

    return success(ctx, {
      token,
      isNewUser,
      userInfo: {
        id: Number(user.id),
        nickName: user.nickName,
        avatarUrl: user.avatarUrl
      }
    })
  } catch (err) {
    if (err.message.startsWith('WeChat API error')) {
      return error(ctx, 400, 'invalid_code', '微信登录失败，code 无效或已过期')
    }
    throw err
  }
}

module.exports = { wxLogin }
