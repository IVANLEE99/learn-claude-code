#!/usr/bin/env node

/**
 * 数据库迁移运行脚本
 * 使用 Prisma 执行迁移
 */

const { execSync } = require('child_process')

async function migrate() {
  console.log('Starting database migration...')

  try {
    // 生成 Prisma Client
    console.log('Generating Prisma Client...')
    execSync('npx prisma generate', { stdio: 'inherit', cwd: __dirname + '/..' })

    // 执行迁移
    console.log('Running migrations...')
    execSync('npx prisma migrate deploy', { stdio: 'inherit', cwd: __dirname + '/..' })

    console.log('Migration completed successfully!')
  } catch (err) {
    console.error('Migration failed:', err.message)
    process.exit(1)
  }
}

migrate()
