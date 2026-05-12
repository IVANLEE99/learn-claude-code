/**
 * 全局错误处理中间件
 */
async function errorHandler(ctx, next) {
  try {
    await next()
  } catch (err) {
    console.error('Server error:', err)

    ctx.status = err.status || 500
    ctx.body = {
      error: 'internal_error',
      message: process.env.NODE_ENV === 'production'
        ? '服务器内部错误'
        : err.message || '服务器内部错误'
    }
  }
}

module.exports = { errorHandler }
