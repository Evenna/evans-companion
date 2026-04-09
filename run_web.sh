#!/usr/bin/env bash
# 在项目根目录启动智脑 Web（前台运行，关闭终端即停止服务）
cd "$(dirname "$0")"
exec uvicorn server:app --host 0.0.0.0 --port 8000
