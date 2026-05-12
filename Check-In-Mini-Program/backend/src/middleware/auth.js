const { verifyToken } = require('../utils/jwt')

/**
 * JWT 鉴权中间件
 * 校验 Authorization: Bearer {token}
 */
function authMiddleware() {
  return async (ctx, next) => {
    const authHeader = ctx.get('Authorization')

    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      ctx.status = 401
      ctx.body = { error: 'unauthorized', message: '请先登录' }
      return
    }

    try {
      const token = authHeader.slice(7)
      const decoded = verifyToken(token)
      ctx.state.userId = decoded.userId
      await next()
    } catch (err) {
      ctx.status = 401
      ctx.body = { error: 'unauthorized', message: '登录已过期，请重新登录' }
    }
  }
}

module.exports = { authMiddleware }
