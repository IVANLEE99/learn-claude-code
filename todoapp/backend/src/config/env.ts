// 环境变量加载与校验

import dotenv from 'dotenv'
import { z } from 'zod'

dotenv.config()

const envSchema = z.object({
  DATABASE_URL: z.string().min(1, 'DATABASE_URL 未配置'),
  JWT_SECRET: z.string().min(1, 'JWT_SECRET 未配置'),
  JWT_EXPIRES_IN: z.string().default('7d'),
  PORT: z.string().default('3000'),
  CORS_ORIGIN: z.string().default('http://localhost:5173'),
})

const parsed = envSchema.safeParse(process.env)

if (!parsed.success) {
  console.error('环境变量校验失败：', parsed.error.format())
  process.exit(1)
}

export const env = parsed.data
