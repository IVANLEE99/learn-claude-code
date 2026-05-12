require('dotenv').config()

const Koa = require('koa')
const bodyParser = require('koa-bodyparser')
const { PrismaClient } = require('@prisma/client')

const authRouter = require('./routes/auth')
const checkinRouter = require('./routes/checkin')
const userRouter = require('./routes/user')
const { errorHandler } = require('./middleware/errorHandler')
const { authMiddleware } = require('./middleware/auth')

const prisma = new PrismaClient()
const app = new Koa()
const PORT = process.env.PORT || 3000

// 全局错误处理
app.use(errorHandler)

// Body parser
app.use(bodyParser())

// 健康检查（无需鉴权）
const Router = require('koa-router')
const healthRouter = new Router()
healthRouter.get('/api/v1/health', (ctx) => {
  ctx.body = {
    data: {
      status: 'ok',
      timestamp: new Date().toISOString()
    },
    message: 'success'
  }
})

// 健康检查路由（无需鉴权）
app.use(healthRouter.routes()).use(healthRouter.allowedMethods())

// 认证路由（无需鉴权）
app.use(authRouter.routes()).use(authRouter.allowedMethods())

// 鉴权中间件（以下路由需要鉴权）
app.use(authMiddleware())

// 业务路由
app.use(checkinRouter.routes()).use(checkinRouter.allowedMethods())
app.use(userRouter.routes()).use(userRouter.allowedMethods())

// 启动服务
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`)
})

// 导出 prisma 实例供其他模块使用
module.exports = { prisma }
