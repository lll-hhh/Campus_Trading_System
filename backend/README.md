# CampuSwap Backend

CampuSwap 后端采用 FastAPI + SQLAlchemy 微服务架构，默认包含以下服务骨架：

- `api_gateway`: 统一入口、鉴权、路由与汇总 API。
- `inventory_service`: 分类、物品、收藏、评论模块。
- `trade_service`: 报价、交易、支付、配送模块。
- `sync_service`: 多库同步、冲突检测、统计。
- `ai_service`: 定价建议、风险识别、语义搜索。
- `monitoring_service`: 报表、告警、健康检查。

目录结构示意：

```
backend/
  apps/
    api_gateway/
    inventory_service/
    trade_service/
    sync_service/
    ai_service/
    monitoring_service/
    core/
    services/
  tests/
```

## 开发环境

```bash
poetry install
poetry run uvicorn apps.api_gateway.main:app --reload
poetry run python -m apps.services.sync_worker  # 单独终端启动同步 worker
```

### 系统依赖

`mysqlclient` 需要系统级头文件与工具，请在 Debian/Ubuntu 上先安装：

```bash
sudo apt update
sudo apt install -y build-essential pkg-config libmariadb-dev
```

如需连接 PostgreSQL，还可以安装 `libpq-dev` 以便本地构建驱动。

可选环境变量：

- `SYNC_STREAM_GROUP`：Redis Stream consumer group（默认 `campuswap-sync-group`）。
- `SYNC_CONSUMER_NAME`：消费者名称，默认主机名，便于水平扩缩容。
- `REDIS_URL` / `*_DSN`：覆盖默认连接串。

## Docker Compose

```bash
docker compose up --build
```

Compose 会启动 API Gateway、各领域服务、`sync_worker` 背景进程以及 Redis/MySQL/MariaDB/Postgres/SQLite。Worker 采用 Redis Streams consumer group，可通过 `docker logs campuswap-sync-worker` 查看日志。

## 角色与权限

- `market_admin`：可触发手动同步、查看/处理冲突、访问高级筛选的全部字段。
- `trader`：可使用高级筛选、查看同步状态（但不可处理冲突）。

在 `users` / `roles` / `user_roles` 表中插入对应数据即可。当管理员登录 `/auth/login` 后将收到带角色声明的 JWT，前端会根据角色动态展示按钮。

## 邮件告警配置

设置以下环境变量即可启用同步冲突邮件提醒：

- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`
- `SMTP_USE_TLS`（默认 `true`）
- `ALERT_SENDER`（可选）
- `ALERT_RECIPIENTS`（逗号分隔列表）

当同步冲突被记录时，系统会向上述收件人发送告警，并在管理端提供“冲突处理”接口。

## 代码规范

- `poetry run black .`
- `poetry run isort .`
- `poetry run flake8`
- `poetry run mypy apps`
- `poetry run pytest`

所有公共函数/类需编写 Google-style docstring，并遵循 zh-google-styleguide。
