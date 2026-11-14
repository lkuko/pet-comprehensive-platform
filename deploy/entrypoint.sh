#!/bin/sh
set -e

echo "[entrypoint] APP_ENV=${APP_ENV:-development}"

echo "[entrypoint] 执行数据库迁移（alembic upgrade head）..."
alembic upgrade head

if [ "${APP_ENV:-development}" != "production" ]; then
  echo "[entrypoint] 非生产环境，执行幂等初始化（管理员/演示数据 + 演示图片复制）..."
  python -m scripts.seed
else
  echo "[entrypoint] 生产环境，跳过 seed（不自动创建演示数据与默认管理员）"
fi

# V1 单实例运行：只启动一个 Uvicorn 进程，保证 APScheduler 仅一个调度器
echo "[entrypoint] 启动 Uvicorn（单实例，单调度器）..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
