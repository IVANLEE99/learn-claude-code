// Express 入口文件

import express from 'express'
import cors from 'cors'
import { env } from './config/env'
import { errorHandler } from './middleware/errorHandler'
import authRoutes from './routes/auth.routes'
import userRoutes from './routes/users.routes'
import listRoutes from './routes/lists.routes'
import todoRoutes from './routes/todos.routes'

const app = express()

// 中间件
app.use(cors({ origin: env.CORS_ORIGIN }))
app.use(express.json())

// 路由挂载
app.use('/api/v1/auth', authRoutes)
app.use('/api/v1/users', userRoutes)
app.use('/api/v1/lists', listRoutes)
app.use('/api/v1/todos', todoRoutes)

// 健康检查
app.get('/api/v1/health', (_req, res) => {
  res.json({ success: true, data: { status: 'ok' } })
})

// 错误处理
app.use(errorHandler)

// 启动
const PORT = parseInt(env.PORT, 10)
app.listen(PORT, () => {
  console.log(`后端服务已启动，端口：${PORT}`)
})

export default app
