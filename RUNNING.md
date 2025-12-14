# 🏃‍♂️ Campus Trading System 运行指南

本指南面向在本地直接运行（非 Docker）的开发者，涵盖后端与前端的启动流程、默认登录账号，以及监控数据模拟脚本的使用方式。

---

## 1. 基础环境要求

| 组件 | 版本建议 | 说明 |
|------|-----------|------|
| Python | 3.10+ | 运行 FastAPI 后端 |
| Node.js | 18+ | 运行 Vite + Vue 前端 |
| 数据库 | MySQL 8.0+ | 至少需要一个主库；可选 PostgreSQL/MariaDB/SQLite 作为同步库 |
| npm | 9+ | 配合 Node.js 安装前端依赖 |

> 💡 初次运行前，请从 `backend/sql/<db>_complete_schema.sql` 与 `backend/sql/<db>_complete_inserts.sql` 导入初始数据，或直接执行 `backend/sql/init/<db>/init.sql`。

---

## 2. 后端（FastAPI）启动步骤

1. **创建并激活虚拟环境**（推荐）
   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate  # Windows 使用 .venv\Scripts\activate
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **配置环境变量**
   ```bash
   cp .env.example .env
   # 修改数据库、JWT、CORS 等选项，至少保证 MySQL 连接正确
   ```

4. **（可选）运行数据库迁移**
   ```bash
   alembic upgrade head
   ```

5. **启动后端服务**
   ```bash
   uvicorn apps.api_gateway.main:app --host 0.0.0.0 --port 8010 --reload
   ```

> ✅ 后端启动后会自动：
> - 初始化数据库对象（触发器、存储过程等）。
> - 触发 `monitoring_data_simulator.ensure_baseline(force=True)`，确保监控类表（performance_metrics、sync_logs、conflict_records、daily_stats 等）具备示例数据。

---

## 3. 前端（Vue + Vite）启动步骤

1. **安装依赖**
   ```bash
   cd frontend
   npm install
   ```

2. **配置 API 代理（按需）**
   - `VITE_API_PROXY_TARGET`：前端开发服务器转发 `/api/v1` 的目标地址（默认 `http://localhost:8010`）。
   - `VITE_IMAGE_PROXY_TARGET`：图片代理目标，默认与 `VITE_API_PROXY_TARGET` 一致。

   可通过在启动命令前导出环境变量或在 `.env` 文件中设置：
   ```bash
   export VITE_API_PROXY_TARGET=http://localhost:8010
   export VITE_IMAGE_PROXY_TARGET=http://localhost:8010
   ```

3. **启动 Vite 开发服务器**
   ```bash
   npm run dev -- --host 0.0.0.0 --port 5173
   ```

   - 若端口被占用可调整为 `5174/5176` 等。
   - 浏览器访问 `http://localhost:5173`（或终端输出的实际端口）。

---

## 4. 默认登录账号

| 角色 | 用户名 | 密码 | 说明 |
|------|--------|------|------|
| 管理员 | `admin` | `admin123` | 拥有后台管理权限，来自 SQL 初始化脚本 |
| 普通用户 | `testuser` | `password123` | 标准用户身份，用于前台体验 |

> 如需新增账号，可通过前端注册流程，或在数据库中插入用户并使用 `apps.core.security.get_password_hash` 生成密码哈希。

---

## 5. 监控数据模拟脚本（Monitoring Data Simulator）

- **文件位置**：`backend/apps/services/monitoring_simulator.py`
- **自动运行时机**：后端启动触发 `monitoring_data_simulator.ensure_baseline(force=True)`，会：
  - 确认 `maintenance_jobs`、`conflict_records` 等表存在并列对齐字段（含 legacy 列 `source_db`/`target_db`）。
  - 生成性能指标、同步日志、冲突记录、每日统计等示例数据。

### 手动刷新监控数据

可在后端虚拟环境中执行以下脚本以重新插入模拟数据：
```bash
cd backend
python - <<'PY'
from apps.services.monitoring_simulator import monitoring_data_simulator
monitoring_data_simulator.ensure_baseline(force=True)
print("Monitoring data refreshed ✔")
PY
```

> 该脚本会依据 `SystemSettingsService` 中的数据库配置遍历多库环境，适用于 demo 数据损坏或需要重新生成时。

---

## 6. 常见问题速查

| 问题 | 解决方案 |
|------|---------|
| 前端登录提示 `getaddrinfo EAI_AGAIN gateway` | 更新 `VITE_API_PROXY_TARGET`，确保代理指向真实后端，如 `http://localhost:8010` |
| 登录返回 401 | 确认使用默认账号，或检查数据库中的 `password_hash` 是否由 `sha256_crypt` 生成 |
| 端口冲突 | 后端可改用 `--port 8011`，前端 `npm run dev -- --port 5174` |

如需进一步部署（Docker/生产环境），请参考 `README.md` 中的“部署指南”章节。
