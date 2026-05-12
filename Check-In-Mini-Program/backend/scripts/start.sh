#!/bin/bash

# 启动脚本
# 用法: ./scripts/start.sh [dev|prod]

MODE=${1:-dev}

echo "Starting Check-In Backend in $MODE mode..."

# 检查 .env 文件
if [ ! -f .env ]; then
  echo "Warning: .env file not found. Copying from .env.example..."
  cp .env.example .env
  echo "Please edit .env with your actual configuration."
  exit 1
fi

# 安装依赖
echo "Installing dependencies..."
npm install

# 运行迁移
echo "Running database migrations..."
npm run migrate

# 启动服务
if [ "$MODE" = "prod" ]; then
  echo "Starting production server..."
  npm start
else
  echo "Starting development server..."
  npm run dev
fi
