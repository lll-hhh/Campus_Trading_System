# CampuSwap 全栈项目

此仓库实现《数据库系统实践》任务书指定的 CampuSwap 平台，包含：

- 多数据库（MySQL、PostgreSQL、MariaDB、SQLite）同步架构
- FastAPI 微服务（网关、库存、交易、同步、AI、监控）
- Vue 3 + TypeScript 管理端界面与移动友好组件
- Redis Streams + APScheduler 事件驱动同步
- 34 张核心数据表设计（见 `docs/requirements-and-tech-selection.md`）

## 目录

```
backend/   # FastAPI + Poetry 微服务代码
frontend/  # Vue3 + Vite + Pinia 前端代码
docs/      # 需求、方案与答辩材料
```

## 快速开始

```bash
docker compose up --build
```

后端默认暴露 `http://localhost:8000`，前端运行在 `http://localhost:5173`。

## 开发模式

后端：
```bash
cd backend
poetry install
poetry run uvicorn apps.api_gateway.main:app --reload
```

前端：
```bash
cd frontend
npm install
npm run dev
```

## 代码规范
- Python：`black`、`isort`、`flake8`、`mypy`
- TypeScript / Vue：`eslint`、`prettier`

## 下一步
- 实现真实数据库模型、Alembic 迁移与 34 张表
- 完成 Redis Stream 消费者与冲突处理 UI
- 补充 AI 训练脚本与移动端可视化
# Campus_Trading_System
