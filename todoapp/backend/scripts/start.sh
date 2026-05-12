#!/bin/bash
# 数据库迁移执行脚本
# 用法：bash scripts/start.sh

set -e

echo "=== 正在同步数据库结构 ==="
npx prisma db push --skip-generate

echo "=== 正在生成 Prisma Client ==="
npx prisma generate

echo "=== 启动后端服务 ==="
exec node dist/index.js
