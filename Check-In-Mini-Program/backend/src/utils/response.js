/**
 * 成功响应
 */
function success(ctx, data, message = 'success') {
  ctx.status = 200
  ctx.body = { data, message }
}

/**
 * 错误响应
 */
function error(ctx, statusCode, errorCode, message) {
  ctx.status = statusCode
  ctx.body = { error: errorCode, message }
}

module.exports = { success, error }
