# 🚀 凤凰汽配商城 运行指南

本项目已简化为单数据库架构（MySQL），去除了冗余的 MariaDB、PostgreSQL 和 SQLite 支持，以提高运行效率和稳定性。

## 🛠️ 环境要求

- Docker & Docker Compose
- Node.js 18+ (可选，用于本地开发)
- Python 3.11+ (可选，用于本地开发)

## ⚡ 快速启动 (推荐)

使用 Docker Compose 一键启动所有服务：

```bash
# 1. 进入项目根目录
cd newkeshe2

# 2. 启动服务
docker compose up -d --build
```

启动后，您可以访问以下地址：

- **前端界面**: [http://localhost:5173](http://localhost:5173)
- **API 文档**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **MySQL 数据库**: `localhost:3306` (用户: root, 密码: campuswap_root)
- **Redis**: `localhost:6379`

## 📝 常用命令

### 查看日志
```bash
docker compose logs -f
```

### 停止服务
```bash
docker compose down
```

### 重置数据库
```bash
docker compose down -v
docker compose up -d
```

## 📂 项目结构

- `backend/`: FastAPI 后端代码
- `frontend/`: Vue 3 前端代码
- `docker-compose.yml`: 容器编排配置
- `backend/sql/init/mysql/init.sql`: 数据库初始化脚本

## ⚠️ 注意事项

1. **数据库初始化**: 首次启动时，MySQL 会自动执行 `backend/sql/init/mysql/init.sql`。如果数据库已存在，则不会重新执行。
2. **AI 功能**: 如需使用 AI 智能定价功能，请在 `.env` 文件中配置 `GLM_API_KEY`。
