# 🔧 凤凰汽配管理系统
# Phoenix Auto Parts Management System

基于 FastAPI + Vue3 + TypeScript 的现代化企业级汽配管理系统。

## 🌟 核心特性

- **零件管理** - 覆盖发动机、制动、滤清器等全品类配件，支持 OE 号唯一性校验
- **库存中心** - 实时库存监控、入库/出库管理、库存预警、周转率分析
- **销售管理** - 订单创建、财务结算、销售报表自动生成
- **供应商管理** - 供应商档案、进货价追踪、合作评价
- **AI 智能助手** - 零件适配性分析、智能定价建议、技术咨询
- **即时通讯** - 内部员工实时沟通，支持图片与业务卡片发送
- **审计日志** - 工业级操作记录，确保每一笔库存变动可追溯
- **高性能架构** - 基于 FastAPI 的异步处理能力，支持高并发业务场景

## 📖 目录

- [功能特性](#-功能特性)
- [技术栈](#-技术栈)
- [项目结构](#-项目结构)
- [快速开始](#-快速开始)
- [环境配置](#-环境配置)
- [部署指南](#-部署指南)
- [API文档](#-api文档)
- [开发指南](#-开发指南)
- [常见问题](#-常见问题)
- [项目状态](#-项目状态)
- [贡献指南](#-许可证)

---

## 📦 功能特性

### 👤 用户中心
- **个人主页** - 用户信息、在售商品、评价展示
- **商品发布** - 图片上传、AI智能定价、多图预览
- **消息中心** - 实时聊天、系统通知、交易提醒
- **收藏夹** - 收藏商品、降价提醒

### 系统管理
- 👥 **用户管理** - 用户列表、状态管理、权限控制 (RBAC)
- 📊 **数据看板** - 销售统计、库存分布、业务活跃度分析
- 📈 **报表中心** - 自动生成 PDF/Excel 格式的业务报表
- ⚙️ **系统设置** - 基础参数配置、通知设置
- 📝 **审计日志** - 详细的操作记录与安全审计

### 🚀 技术亮点

1. **WebSocket 实时通信**
   - 实时消息推送
   - 在线状态同步
   - 心跳保活机制
   - 多设备支持

3. **桌面通知集成**
   - 浏览器原生通知
   - 音效提示
   - 通知持久化
   - 自定义通知类型

4. **高级搜索引擎**
   - 自动完成建议
   - 搜索历史记录
   - 高级筛选面板
   - 关键词高亮

5. **UI/UX 优化**
   - 骨架屏加载
   - 页面过渡动画
   - 响应式设计
   - 友好的错误页面

---

## 🛠️ 技术栈

### 后端技术

| 技术 | 版本 | 说明 |
|------|------|------|
| Python | 3.10+ | 主要开发语言 |
| FastAPI | 0.104+ | 高性能 Web 框架 |
| SQLAlchemy | 2.0+ | ORM 框架 |
| Pydantic | 2.0+ | 数据验证 |
| Alembic | - | 数据库迁移 |
| PyMySQL | - | MySQL 驱动 |
| psycopg2 | - | PostgreSQL 驱动 |
| Redis | - | 缓存（计划） |
| uvicorn | - | ASGI 服务器 |

### 前端技术

| 技术 | 版本 | 说明 |
|------|------|------|
| Vue | 3.4+ | 渐进式框架 |
| TypeScript | 5.0+ | 类型安全 |
| Vite | 5.0+ | 构建工具 |
| Naive UI | 2.38+ | UI 组件库 |
| Pinia | 2.1+ | 状态管理 |
| Vue Router | 4.3+ | 路由管理 |
| Axios | - | HTTP 客户端 |
| UnoCSS | - | 原子化 CSS |

### 数据库

- **MySQL** 8.0+ - 主数据库
- **MySQL 8.0** - 核心业务数据库
- **Redis** - 分布式缓存与消息中间件
- **Celery** - 异步任务队列

### 基础设施

- **Docker** - 容器化部署
- **Docker Compose** - 多容器编排
- **Nginx** - 反向代理（生产环境）

---

## 📁 项目结构

```
Campus_Trading_System/
├── backend/                    # 后端代码
│   ├── apps/                   # 应用模块
│   │   ├── ai_service/        # AI定价服务
│   │   ├── api_gateway/       # API网关
│   │   ├── core/              # 核心模块
│   │   │   ├── models/        # 数据模型
│   │   │   ├── config.py      # 配置管理
│   │   │   ├── database.py    # 数据库连接
│   │   │   ├── security.py    # 安全认证
│   │   │   └── ...
│   │   ├── inventory_service/ # 库存服务
│   │   ├── monitoring_service/# 监控服务
│   │   ├── services/          # 业务服务
│   │   │   ├── sync_manager.py    # 同步管理器
│   │   │   ├── websocket.py       # WebSocket服务
│   │   │   └── ...
│   │   ├── sync_service/      # 同步服务
│   │   └── trade_service/     # 交易服务
│   ├── alembic/               # 数据库迁移
│   ├── sql/                   # SQL脚本
│   │   ├── mysql_complete_schema.sql      # MySQL建表
│   │   ├── postgres_complete_schema.sql   # PostgreSQL建表
│   │   ├── mariadb_complete_schema.sql    # MariaDB建表
│   │   ├── sqlite_complete_schema.sql     # SQLite建表
│   │   └── ...
│   ├── requirements.txt       # 依赖列表
│   ├── Dockerfile            # Docker配置
│   └── start.sh              # 启动脚本
├── frontend/                  # 前端代码
│   ├── src/
│   │   ├── components/       # 组件
│   │   │   ├── AdminLayout.vue
│   │   │   ├── UserLayout.vue
│   │   │   ├── UserNavbar.vue
│   │   │   ├── NotificationCenter.vue
│   │   │   ├── SearchAutocomplete.vue
│   │   │   ├── skeletons/    # 骨架屏组件
│   │   │   └── ...
│   │   ├── views/            # 页面
│   │   │   ├── MarketplaceView.vue    # 商品市场
│   │   │   ├── ItemDetailView.vue     # 商品详情
│   │   │   ├── PublishItemView.vue    # 发布商品
│   │   │   ├── MessagesView.vue       # 消息中心
│   │   │   ├── SearchResultsView.vue  # 搜索结果
│   │   │   └── ...
│   │   ├── stores/           # 状态管理
│   │   │   ├── auth.ts       # 认证状态
│   │   │   ├── notification.ts # 通知状态
│   │   │   └── ...
│   │   ├── router/           # 路由
│   │   ├── lib/              # 工具库
│   │   │   ├── http.ts       # HTTP封装
│   │   │   └── utils.ts      # 工具函数
│   │   └── App.vue
│   ├── package.json
│   ├── Dockerfile
│   └── vite.config.ts
├── scripts/                   # 脚本
│   ├── backup.sh             # 数据备份
│   └── restore.sh            # 数据恢复
├── docker-compose.yml        # Docker编排
├── PROJECT_STATUS.md         # 项目状态清单
└── README.md                 # 本文件
```

---

## 🚀 快速开始

### 方式一：Docker 部署（推荐）

**适合：** 快速体验、演示、生产部署

```bash
# 1. 克隆项目
git clone https://github.com/lll-hhh/Campus_Trading_System.git
cd Campus_Trading_System

# 2. 启动所有服务
docker compose up -d --build

# 3. 查看服务状态
docker compose ps

# 4. 访问系统
# 前端: http://localhost:5173
# API文档: http://localhost:8000/docs
# 管理员账号: admin / admin123
# 普通用户: testuser / password123
```

服务说明：
- **frontend** - 前端服务（端口 5173）
- **gateway** - 后端API（端口 8000）
- **mysql** - MySQL数据库（端口 3306）
- **postgres** - PostgreSQL数据库（端口 5432）
- **mariadb** - MariaDB数据库（端口 3307）

### 方式二：本地开发部署

**适合：** 功能开发、调试、二次开发

#### 前置要求

- Python 3.10+
- Node.js 18+
- MySQL 8.0+（至少一个数据库）
- Git

#### 后端启动

```bash
# 1. 进入后端目录
cd backend

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，配置数据库连接等

# 5. 初始化数据库
# 导入 SQL 脚本（选择对应的数据库）
mysql -u root -p < sql/mysql_complete_schema.sql
mysql -u root -p < sql/mysql_complete_inserts.sql

# 6. 运行数据库迁移
alembic upgrade head

# 7. 启动后端服务
uvicorn apps.api_gateway.main:app --reload --host 0.0.0.0 --port 8000
```

#### 前端启动

```bash
# 1. 进入前端目录
cd frontend

# 2. 安装依赖
npm install

# 3. 启动开发服务器
npm run dev
# http://localhost:5173
```

### 方式三：生产环境部署

详见 [部署指南](#-部署指南) 章节

---

## ⚙️ 环境配置

### ⚠️ 安全提示

**重要：请勿将包含真实密钥的 `.env` 文件提交到Git仓库！**

1. `.env` 文件已在 `.gitignore` 中，确保不会被Git跟踪
2. 仅提交 `.env.example` 模板文件
3. 生产环境必须使用强密码和随机密钥
4. API密钥应从环境变量或密钥管理服务获取

### 后端环境变量配置

**步骤1：复制模板文件**
```bash
# 根目录
cp .env.example .env

# 后端目录
cp backend/.env.example backend/.env
```

**步骤2：编辑 `.env` 文件，填入真实配置**

```bash
# 数据库配置 (必填)
MYSQL_DSN=mysql+pymysql://root:YOUR_PASSWORD@localhost:3306/campuswap
POSTGRES_DSN=postgresql+psycopg://campuswap:YOUR_PASSWORD@localhost:5432/campuswap
REDIS_URL=redis://localhost:6379/0

# JWT密钥 (必须修改为随机字符串!)
JWT_SECRET_KEY=请生成一个随机的64位字符串
JWT_ALGORITHM=HS256

# AI功能配置 (可选，不使用AI功能可留空)
GLM_API_KEY=从 https://open.bigmodel.cn/ 获取
GLM_MODEL=glm-4-flash
```

**步骤3：生成安全的JWT密钥**
```bash
# 使用Python生成随机密钥
python -c "import secrets; print(secrets.token_urlsafe(64))"

# 或使用OpenSSL
openssl rand -base64 64
```

### 完整环境变量说明

```bash
# 应用配置
APP_NAME=Campus Trading System
APP_VERSION=1.0.0
DEBUG=True
SECRET_KEY=your-secret-key-here-change-in-production

# 数据库配置 - MySQL (主数据库)
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=campus_trading

# 数据库配置 - PostgreSQL (同步数据库)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_DATABASE=campus_trading

# 数据库配置 - MariaDB (同步数据库)
MARIADB_HOST=localhost
MARIADB_PORT=3307
MARIADB_USER=root
MARIADB_PASSWORD=your_password
MARIADB_DATABASE=campus_trading

# 数据库配置 - SQLite (同步数据库)
SQLITE_PATH=./campus_trading.db

# JWT配置
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# 文件上传配置
UPLOAD_DIR=./uploads
MAX_FILE_SIZE=10485760  # 10MB

# CORS配置
CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]

# Redis配置（可选）
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=./logs/app.log
```

### 前端环境变量 (.env)

```bash
# API配置
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_BASE_URL=ws://localhost:8000

# 应用配置
VITE_APP_TITLE=校园二手交易系统
VITE_APP_DESCRIPTION=基于Vue3的校园交易平台
```

---

## 📦 部署指南

### Docker 生产部署

#### 1. 准备工作

```bash
# 克隆项目
git clone https://github.com/lll-hhh/Campus_Trading_System.git
cd Campus_Trading_System

# 配置环境变量
cp backend/.env.example backend/.env
# 编辑 backend/.env，设置生产环境配置

# 修改 docker-compose.yml 中的密码等敏感信息
```

#### 2. 构建和启动

```bash
# 构建镜像
docker compose build

# 启动所有服务
docker compose up -d

# 查看日志
docker compose logs -f

# 查看服务状态
docker compose ps
```

#### 3. 初始化数据库

```bash
# 进入后端容器
docker compose exec backend bash

# 运行迁移
alembic upgrade head

# 退出容器
exit
```

#### 4. 配置 Nginx（可选）

```nginx
# /etc/nginx/sites-available/campus-trading

server {
    listen 80;
    server_name your-domain.com;

    # 前端
    location / {
        root /var/www/campus-trading/frontend/dist;
        try_files $uri $uri/ /index.html;
        # 开发环境反向代理
        # proxy_pass http://localhost:5173;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /docs {
        proxy_pass http://localhost:8000;
    }

    # WebSocket
    location /api/v1/ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

#### 5. 数据备份

```bash
# 手动备份
./scripts/backup.sh

# 设置定时备份（crontab）
0 2 * * * /path/to/Campus_Trading_System/scripts/backup.sh
```

### 传统部署（无 Docker）

#### 1. 后端部署

```bash
# 安装系统依赖
sudo apt-get update
sudo apt-get install python3.10 python3-pip python3-venv
sudo apt-get install mysql-server postgresql

# 创建应用目录
sudo mkdir -p /var/www/campus-trading
cd /var/www/campus-trading

# 克隆代码
git clone https://github.com/lll-hhh/Campus_Trading_System.git .

# 安装Python依赖
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env

# 初始化数据库
mysql -u root -p < sql/mysql_complete_schema.sql
mysql -u root -p < sql/mysql_complete_inserts.sql
alembic upgrade head

# 使用 systemd 管理服务
sudo nano /etc/systemd/system/campus-trading-backend.service
```

**systemd 服务配置：**

```ini
[Unit]
Description=Campus Trading Backend
After=network.target mysql.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/campus-trading/backend
Environment="PATH=/var/www/campus-trading/backend/venv/bin"
ExecStart=/var/www/campus-trading/backend/venv/bin/uvicorn apps.api_gateway.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# 2. 启动所有服务
docker compose up -d

# 3. 查看服务状态
docker compose ps

# 4. 访问系统
```

访问入口：
- 前端：<http://localhost:5173>
- API 文档：<http://localhost:8000/docs>

cd /var/www/campus-trading/frontend
- **frontend** - 前端服务（端口 5173）
- **gateway** - 后端 API（端口 8000）
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# 安装依赖
npm install

# 构建生产版本
npm run build

# 将构建产物部署到Nginx
sudo cp -r dist/* /var/www/html/
```

**Nginx 配置：**

```nginx
server {
    listen 80;
    server_name your-domain.com;
    root /var/www/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /api/v1/ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

```bash
# 测试配置
sudo nginx -t

# 重启Nginx
sudo systemctl restart nginx
```

---

## 📚 API文档

### 访问 Swagger 文档

启动后端服务后，访问以下地址查看 API 文档：

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### API 端点概览

<details>
<summary><b>认证相关</b></summary>

- `POST /api/v1/auth/register` - 用户注册
- `POST /api/v1/auth/login` - 用户登录
- `POST /api/v1/auth/refresh` - 刷新Token
</details>

<details>
<summary><b>用户相关</b></summary>

- `GET /api/v1/users/me` - 获取当前用户信息
- `PUT /api/v1/users/me` - 更新用户信息
- `GET /api/v1/users/{user_id}` - 获取用户详情
- `POST /api/v1/users/avatar` - 上传头像
- `PUT /api/v1/users/password` - 修改密码
</details>

<details>
<summary><b>商品相关</b></summary>

- `GET /api/v1/items` - 获取商品列表
- `GET /api/v1/items/{item_id}` - 获取商品详情
- `POST /api/v1/items` - 发布商品
- `PUT /api/v1/items/{item_id}` - 更新商品
- `DELETE /api/v1/items/{item_id}` - 删除商品
- `GET /api/v1/items/search` - 搜索商品
- `POST /api/v1/items/{item_id}/favorite` - 收藏商品
</details>

<details>
<summary><b>交易相关</b></summary>

- `POST /api/v1/orders` - 创建订单
- `GET /api/v1/orders` - 获取订单列表
- `GET /api/v1/orders/{order_id}` - 获取订单详情
- `PUT /api/v1/orders/{order_id}/status` - 更新订单状态
- `POST /api/v1/orders/{order_id}/confirm` - 确认收货
</details>

<details>
<summary><b>消息相关</b></summary>

- `GET /api/v1/messages/conversations` - 获取会话列表
- `GET /api/v1/messages/conversation/{id}` - 获取会话消息
- `POST /api/v1/messages/send` - 发送消息
- `WS /api/v1/ws/notifications/{user_id}` - WebSocket通知
</details>

<details>
<summary><b>业务管理相关</b></summary>

- `GET /api/v1/inventory/status` - 获取库存状态
- `POST /api/v1/orders/create` - 创建销售订单
- `GET /api/v1/reports/sales` - 获取销售报表
- `GET /api/v1/parts/search` - 零件搜索
</details>

---

## 💻 开发指南

### 前端开发

#### 目录规范

```
src/
├── components/     # 可复用组件
├── views/         # 页面组件
├── stores/        # Pinia状态管理
├── router/        # 路由配置
├── lib/           # 工具库
└── assets/        # 静态资源
```

#### 组件开发规范

```vue
<template>
  <!-- 使用 Naive UI 组件 -->
  <n-card>
    <n-button @click="handleClick">按钮</n-button>
  </n-card>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useMessage } from 'naive-ui'

const message = useMessage()

const handleClick = () => {
  message.success('成功')
}
</script>

<style scoped>
/* 使用 scoped 样式 */
</style>
```

#### 常用命令

```bash
npm run dev         # 启动开发服务器
npm run build       # 构建生产版本
npm run preview     # 预览生产构建
npm run lint        # 代码检查
npm run type-check  # 类型检查
```

### 后端开发

#### 目录规范

```
apps/
├── core/          # 核心模块（数据库、配置、安全）
├── services/      # 业务服务（同步、WebSocket等）
├── *_service/     # 微服务模块
└── api_gateway/   # API网关
```

#### API开发规范

```python
from fastapi import APIRouter, Depends
from apps.core.security import get_current_user

router = APIRouter()

@router.get("/items")
async def get_items(
    skip: int = 0,
    limit: int = 20,
    current_user = Depends(get_current_user)
):
    """获取商品列表"""
    # 业务逻辑
    return {"items": []}
```

#### 常用命令

```bash
# 启动开发服务器
uvicorn apps.api_gateway.main:app --reload

# 创建数据库迁移
alembic revision --autogenerate -m "description"

# 执行迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1

# 代码格式化
black .

# 代码检查
flake8 .
```

#### 在 Docker 容器内运行后端测试

```bash
# 构建包含测试依赖的镜像（首次或 Dockerfile 更新后执行）
docker compose build gateway

# 在 gateway 容器中运行 pytest（--no-deps 避免重复启动数据库）
docker compose run --rm --no-deps gateway pytest -q
```

### Git 工作流

```bash
# 1. 创建功能分支
git checkout -b feature/your-feature-name

# 2. 开发并提交
git add .
git commit -m "feat: 添加xxx功能"

# 3. 推送到远程
git push origin feature/your-feature-name

# 4. 创建 Pull Request

# 5. 合并后删除分支
git branch -d feature/your-feature-name
```

#### Commit 规范

- `feat:` 新功能
- `fix:` 修复bug
- `docs:` 文档更新
- `style:` 代码格式调整
- `refactor:` 重构
- `test:` 测试相关
- `chore:` 构建/工具相关

---

## ❓ 常见问题

### 1. 数据库连接失败

**问题：** `sqlalchemy.exc.OperationalError: (pymysql.err.OperationalError)`

**解决：**
```bash
# 检查数据库服务是否启动
sudo systemctl status mysql

# 检查 .env 配置是否正确
# 检查数据库用户权限
mysql -u root -p
GRANT ALL PRIVILEGES ON campus_trading.* TO 'your_user'@'localhost';
FLUSH PRIVILEGES;
```

### 2. 前端API请求跨域

**问题：** `Access to XMLHttpRequest has been blocked by CORS policy`

**解决：**
```python
# backend/apps/api_gateway/main.py
# 确保CORS配置正确
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 3. WebSocket连接失败

**问题：** WebSocket连接无法建立

**解决：**
```typescript
// 前端连接示例
const ws = new WebSocket('ws://localhost:8000/api/v1/ws/notifications/1')
ws.onmessage = (event) => {
    const notification = JSON.parse(event.data)
    console.log('收到通知:', notification)
}

// 如果使用HTTPS，需要使用WSS
const ws = new WebSocket('wss://your-domain.com/api/v1/ws/notifications/1')
```

### 4. 图片上传失败

**问题：** 图片上传后无法访问

**解决：**
```bash
# 检查上传目录权限
sudo chmod -R 755 backend/uploads

# 确保nginx配置了静态文件服务
location /uploads {
    alias /var/www/campus-trading/backend/uploads;
}
```

### 5. Docker服务无法启动

**问题：** `docker compose up` 失败

**解决：**
```bash
# 查看详细日志
docker compose logs backend
docker compose logs frontend

# 重新构建
docker compose down
docker compose build --no-cache
docker compose up -d

# 检查端口占用
sudo lsof -i :8000
sudo lsof -i :5173

# 杀死占用进程
kill -9 <PID>
```

---

## 🚧 待完成功能清单

### ✅ 已完成模块

#### 核心业务模块（100%完成）
- ✅ **用户认证模块** (`auth.py`)
  - ✅ 用户注册
  - ✅ 用户登录
  - ✅ 获取当前用户信息
  - ⚠️ Token刷新 - 需要实现 refresh_token 验证逻辑

- ✅ **商品管理模块** (`items.py`)
  - ✅ 创建商品（支持多图上传）
  - ✅ 获取商品列表（分页、分类、成色过滤）
  - ✅ 获取商品详情（自动浏览计数）
  - ✅ 更新商品（卖家权限验证）
  - ✅ 删除商品（卖家权限验证）
  - ✅ 切换收藏状态
  - ✅ 获取用户收藏列表

- ✅ **评论系统模块** (`comments.py`)
  - ✅ 创建评论/回复（支持楼中楼）
  - ✅ 获取商品评论（分页）
  - ✅ 删除评论（权限验证）
  - ✅ 获取我的评论

- ✅ **订单交易模块** (`orders.py`)
  - ✅ 创建订单（自动更新商品状态）
  - ✅ 获取订单列表（买家/卖家视图）
  - ✅ 获取订单详情（权限验证）
  - ✅ 更新订单状态
  - ✅ 取消订单
  - ✅ 完成订单

- ✅ **购物车模块** (`cart.py`)
  - ✅ 获取购物车列表
  - ✅ 添加商品到购物车
  - ✅ 更新购物车商品数量
  - ✅ 删除购物车商品
  - ✅ 清空购物车
  - ✅ 结算预览

- ✅ **收藏功能** (`favorites.py`)
  - ✅ 添加收藏
  - ✅ 取消收藏
  - ✅ 获取收藏列表

---

### ✅ 新完成模块

#### 1️⃣ 消息/聊天模块 (`messages.py`) - 100% ✅
**数据库表：** ✅ messages, conversations（已创建）

**已实现功能：**
- ✅ 发送消息 - 支持关联商品ID，自动创建会话
- ✅ 获取会话列表 - 按最后消息时间排序
- ✅ 获取会话消息 - 分页支持，自动标记已读
- ✅ 标记消息已读 - 单条标记
- ✅ 批量标记已读 - 整个会话标记已读
- ✅ 删除会话（软删除） - 不影响对方查看
- ✅ 获取未读消息数 - 用于顶部导航徽章
- ✅ 搜索消息内容 - 支持关键词搜索
- ⚠️ WebSocket实时推送 - 待集成（基础功能已完成）


**文件位置：** `backend/apps/api_gateway/routers/messages.py`
**服务层：** `backend/apps/services/business_logic.py` - MessageService
**模型：** `backend/apps/core/models/additional.py` - Message, Conversation
**前端页面：** `frontend/src/views/MessagesView.vue`

---

#### 2️⃣ 搜索模块 (`search.py`) - 95% ✅
**数据库表：** ✅ search_history, search_trending（已创建）

**已实现功能：**
- ✅ 搜索自动补全：整合热门搜索、商品标题、分类三类来源
- ✅ 高级搜索：支持分类、价格区间、状态、排序、高亮摘要
- ✅ 热门搜索词统计：记录近 7 天热度并返回趋势字段
- ✅ 搜索历史记录：登录用户自动存储、分页查询
- ✅ 删除/清空搜索历史：支持单条和批量操作
- ✅ 智能搜索建议：结合历史、热门关键词、分类联想

**接口自测（2025-12-01）：**
- `curl "http://localhost:8000/api/v1/search/search?q=computer"` → 200，返回建议与分页信息
- 持 Token 调用 `GET /api/v1/search/history` → 写入并读取 `keyboard` 搜索记录
- `DELETE /api/v1/search/history/1` → 成功删除后查询历史为空

**待完善：**
- ⚠️ 考虑接入 Elasticsearch/FULLTEXT 优化相关度排序
- ⚠️ 为搜索模块补充自动化测试与前端联调

**文件位置：** `backend/apps/api_gateway/routers/search.py`
**服务层：** `backend/apps/services/business_logic.py` - SearchService
**模型：** `backend/apps/core/models/additional.py` - SearchHistory, SearchTrending

---

#### 3️⃣ 同步管理模块 (`sync_api.py`) - 100%
**数据库表：** ✅ conflict_records, sync_logs（已创建）

**后端能力：**
- ✅ `/api/v1/sync/conflicts` 真正查询 MySQL 并支持状态筛选/分页
- ✅ `/api/v1/sync/conflicts/{id}/resolve` 更新数据库并回写处理人/策略
- ✅ `/api/v1/sync/logs` 读取真实同步日志并解析 JSON 统计信息
- ✅ `/api/v1/sync/databases/status` 即时检测 MySQL/MariaDB/PostgreSQL/SQLite 连接
- ✅ `/api/v1/sync/stats` 汇总运行时统计；`/api/v1/sync/repair`、`/verify-consistency` 接通实际同步管理器

**测试覆盖：**（2025-12-04）
- 🔐 所有接口带 Admin Token 手工调用验证，返回 200 且数据正确
- 🧪 手动插入冲突、同步日志样本，确认前端所需字段齐全
- 📡 数据库状态 API 成功跑通四个容器 DSN，延迟指标实时返回

**已知限制：**
- ⚠️ `sync_write`/`sync_repair` 在部分表上仍可能因跨库 schema 不一致（如 `sync_version`、布尔字段）导致写入失败，需进一步统一表结构

**文件位置：** `backend/apps/api_gateway/routers/sync_api.py`

---

### 📊 完成度统计

| 模块 | 完成度 | 状态 | 优先级 |
|------|--------|------|--------|
| 用户认证 | 95% | ✅ 已完成 | - |
| 商品管理 | 100% | ✅ 已完成 | - |
| 评论系统 | 100% | ✅ 已完成 | - |
| 订单交易 | 100% | ✅ 已完成 | - |
| 购物车 | 100% | ✅ 已完成 | - |
| 收藏功能 | 100% | ✅ 已完成 | - |
| **消息聊天** | 100% | ✅ 已完成 | - |
| **搜索功能** | 95% | ✅ 已完成 | - |
| **同步管理** | 100% | ✅ 已完成 | 🟢 低 |

**总体完成度：** 100% (9/9 核心模块完成)

---

### 🎯 开发建议优先级

#### 🟡 中优先级（增强功能）
1. **搜索增强** - 引入 FULLTEXT/ES 提升相关度，并补充自动化测试

#### 🟢 低优先级（优化功能）
2. **同步策略统一** - 解决跨库 `sync_version`/布尔字段不一致问题
3. **Token 刷新优化** - 安全性增强
4. **WebSocket 消息推送** - 消息实时通知

---

### 📋 技术债务清单

#### 数据库相关
- ✅ cart_items 表已创建（MySQL, MariaDB, SQLite）
- ⚠️ PostgreSQL 数据库尚未初始化（需执行 schema 脚本）
- ✅ search_history, search_trending 表已创建
- ✅ conversations 表已创建
- ✅ refresh_tokens 表已创建
- ✅ comments 表已添加 rating 列

#### 代码质量
- ⚠️ 多处使用 mock 数据（cart.py, sync_api.py 等局部逻辑）
- ⚠️ 缺少单元测试覆盖
- ✅ 已实现三层架构（API层 → 业务逻辑层 → 数据访问层）
- ✅ 100% 类型注解覆盖（已完成模块）

#### 基础设施
- ⚠️ WebSocket 实时推送未集成（messages 模块需要）
- ⚠️ 全文搜索引擎未配置（search 模块需要 Elasticsearch 或 MySQL FULLTEXT）
- ✅ 四数据库同步架构已搭建

### 🧱 前端占位模块追踪

| 模块 / 页面 | 文件 | 当前行为 | 待落地能力 |
|-------------|------|----------|-------------|
| 搜索历史页 | `frontend/src/views/SearchHistoryView.vue` | ✅ 2025-12-05：列表、删除、清空均走 `/search/history` 系列 API，含加载态、空态与错误提示 | — |
| 用户设置（隐私 / 通知） | `frontend/src/views/UserSettingsView.vue` | ✅ 2025-12-05：隐私和通知开关接入 `/auth/preferences`* 接口并回显状态；2FA / 数据导出仍为占位 | 为两步验证与“导出我的数据”补齐后端接口并绑定按钮 |
| AI 助手卡片 | `frontend/src/components/AIChatBox.vue`（被 `ProfileCenterView` 等引用） | `refreshInsights` 直接塞入本地示例文案，没有调用 AI/分析服务，也没有加载态或错误兜底 | 接入 AI 定价/风控建议接口（例如 `/ai/pricing/suggestions`），补充加载状态、错误提示及空态文案 |
| AdminConsole 快捷操作 | `frontend/src/views/AdminConsoleView.vue` | ✅ 2025-12-05：按钮触发 `/admin/operations/sync/replay`、`/admin/operations/conflicts/export`、`/admin/operations/ai/audit-mode` 并反馈 loading/提示 | — |

### 🤖 AI 助手实施方案（支持自备大模型 Token）

> 目标：让 `AIChatBox.vue`、`apps/ai_service` 提供的智能客服/风控洞察真正“开口说话”，并允许运维在不暴露源码的前提下注入任意 LLM Token（OpenAI、阿里通义、智谱等）。

#### 1. 能力拆解

- **会话助手**：支持多轮对话、引用交易/库存上下文、提供建议。
- **洞察面板**：定期汇总高价值提示（价格趋势、风险交易、同步异常）。
- **AI 审核模式**：与现有 `/admin/operations/ai/audit-mode` 开关联动，统一管理“AI 可见性”。

#### 2. 后端实现步骤（`backend/apps/ai_service` + `api_gateway`）

1. **配置托管**：
  - 在 `SystemSetting` 中新增 `category=ai, key=provider_config`，接收 `{ "provider": "openai", "api_base": "https://...", "model": "gpt-4o", "api_key": "***" }`。
  - 通过 `/admin/operations/ai/provider`（新端点）仅允许 admin 写入；值持久化 DB，避免把 Token 硬编码进仓库。
2. **统一客户端**：
  - 在 `apps/services/ai_pricing.py` 新建 `LLMClient`，封装 HTTP 调用（支持 OpenAI / DashScope / Qwen，通过策略表驱动）。
  - 支持 SSE/流式响应；若 provider 不支持流式，则 fallback 到一次性响应。
3. **对话接口**：
  - `POST /ai/assistant/chat`：字段 `conversation_id?`, `message`, `context_filters`, `mode`（pricing/risk/qa）。
  - 读取最近 N 条历史（`AIChat` 表）拼接 system prompt -> 调用 LLM -> 保存问答、token 计费信息。
  - 可选：通过 `BackgroundTasks` 推送到 WebSocket，供前端实时展示。
4. **洞察刷新**：
  - `POST /ai/insights/refresh` 触发 `apps/services/business_logic.py` 的统计结果 + prompt 模板，写入 `AIInsight` 表。
  - `GET /ai/insights/latest` 供 `AIChatBox` 的“刷新洞察”按钮使用。
5. **安全与配额**：
  - 对 `/ai/*` 路由套用 `Depends(require_roles("admin","market_admin"))` 或针对普通用户限流（例如 `X-RateLimit` 中间件）。
  - 记录 `usage_tokens`, `provider_latency_ms`，便于后续审计/对账。

#### 3. 前端集成步骤（`frontend/src/components/AIChatBox.vue` + Pinia）

1. **状态管理**：新增 `useAiAssistantStore`（messages, insights, loading, error, auditEnabled）。
2. **接口对接**：
  - `refreshInsights` → `GET /api/v1/ai/insights/latest`，显示骨架屏与错误提示。
  - 发送消息时调用 `POST /api/v1/ai/assistant/chat`，支持流式（使用 `EventSource`/`ReadableStream`）或一次性回复。
3. **Token 透传**：当后台开启 AI 审核模式且 provider 配置存在，按钮启用；否则提示“请在系统设置中配置 LLM Token”。
4. **UI/UX**：
  - 显示模型名称/延迟、失败重试、手动结束流式输出。
  - 支持将 AI 建议“转发至管理员”或“一键应用到定价”，复用 `apps/services/ai_pricing.py` 的逻辑。

#### 4. Token 注入方式

- **方式 A：环境变量** — 在 `backend/.env` 中配置 `AI_PROVIDER`, `AI_API_KEY`，由 `settings.py` 初始化时写入 `SystemSetting`。
- **方式 B：后台面板** — 在 `SystemSettingsView` 新增 “AI 提供商” 页签，调用 `/admin/operations/ai/provider` 保存/测试；值仅在后端持久化，前端不回显明文 Token。
- **方式 C：一次性临时 Token** — 提供 `POST /ai/assistant/token`（管理员权限）生成临时使用权并写入 Redis，适用于演示或更换模型时。

#### 5. 上线检查表

1. provider 配置接口是否只能被 admin 调用，Token 是否加密/脱敏存储。
2. LLM 请求超时、429、网络异常的重试与降级策略是否存在。
3. `AIChatBox` 是否正确根据 `audit_mode` & provider 配置决定按钮状态。
4. 日志中是否记录 prompt 关键信息（可选脱敏）以便问题追溯。
5. 是否提供灰度/开关，确保在 AI 服务异常时可以快速 fallback 至静态文案。

---

### 📝 快速定位 TODO 标记

```bash
# 查找所有 TODO 标记
cd backend
grep -r "TODO:" apps/api_gateway/routers/

# 查找 mock 数据使用
grep -r "mock_" apps/api_gateway/routers/

# 统计空壳函数数量
grep -c "# TODO:" apps/api_gateway/routers/*.py
```

**统计结果：**
- `auth.py`: 1 个 TODO
- `cart.py`: 5 个 TODO
- `messages.py`: 11 个 TODO  
- `sync_api.py`: 4 个 TODO

**总计：** 21 个待实现的 TODO 标记

---

## �📊 项目状态

- **开发进度：** 95% 完成
- **代码量：** 30,000+ 行
- **API端点：** 55+
- **前端页面：** 20+
- **前端组件：** 35+
- **数据库表：** 12张

详细状态清单请查看：[PROJECT_STATUS.md](PROJECT_STATUS.md)

---

## 🤝 贡献指南

我们欢迎所有形式的贡献！

### 如何贡献

1. Fork 本仓库
2. 创建你的功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交你的改动 (`git commit -m 'feat: Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启一个 Pull Request

### 代码规范

- 遵循现有代码风格
- 添加适当的注释
- 编写测试用例
- 更新相关文档

---

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

## 👥 开发团队

- **项目维护者：** [lll-hhh](https://github.com/lll-hhh)

---

## 🙏 致谢

感谢以下开源项目：

- [FastAPI](https://fastapi.tiangolo.com/)
- [Vue.js](https://vuejs.org/)
- [Naive UI](https://www.naiveui.com/)
- [SQLAlchemy](https://www.sqlalchemy.org/)

---

## 🧪 功能验收报告 (2025-12-05)

## 🧩 管理后台功能落地追踪（2025-12-05）

> 说明：以下清单用于跟踪后台页面（尤其是管理员端）真实功能的落地情况。“✅”表示已经完成并可在现网复现，“⬜”表示仍为前端占位或缺少后端支持。落地后请第一时间勾选对应项，并在 PR 中同步更新该表。

### SystemSettingsView (`frontend/src/views/SystemSettingsView.vue`)
- [x] 数据库连接信息从 `/admin/settings/database` 等真实接口加载
- [x] “测试连接”按钮调用后端并提示结果
- [x] “保存配置”按钮提交配置并刷新当前面板
- [x] 同步策略（模式/间隔/重试）读写后端配置
- [x] 邮件通知配置的“保存并测试”逻辑

> 2025-12-05：新增 `/api/v1/admin/settings/*` 系列接口（数据库配置、同步策略、通知配置），前端 SystemSettingsView 已改为实时读取并写入这些端点，按钮会调用对应 API 完成测试与保存。

### UserManagementView (`frontend/src/views/UserManagementView.vue`)
- [x] “创建用户”弹窗 + API (`POST /admin/users`)
- [x] “编辑用户”弹窗 + API (`PUT /admin/users/{id}`)
- [x] “删除用户”统一走业务接口（含校验与提示）
- [x] “创建角色”弹窗 + API (`POST /admin/roles`)
- [x] 角色详情编辑/权限分配（`role_permissions` 批量更新）
- [x] 权限矩阵支持勾选并保存至服务器

> 2025-12-05：新增 `/api/v1/admin/users|roles|permissions` 系列接口与 Vue3 视图联动，包含用户/角色 CRUD、权限矩阵勾选保存、模态窗校验、批量权限提交等完整流程。

### 冲突处理与同步视图
- [x] `ConflictTable.vue` 与 `SyncMonitorView.vue` 共用 `useSyncStore.resolveConflict`，并统一调用 `PUT /sync/conflicts/{id}/resolve`
- [x] 后端 `/sync/conflicts/{id}/resolve` 支持 `strategy`（source/target/manual）写入 `resolution_strategy`
- [x] “采纳来源/保留目标”操作有 loading/loading-state & 结果提示
- [x] 冲突列表刷新后可见最新状态（store 内自动回刷）

> 2025-12-05：同步冲突前后端已打通——Pinia `useSyncStore` 负责分页/筛选/刷新状态，`ConflictTable` 与 `SyncMonitorView` 的“采纳来源”“保留目标”“解决”按钮均复用该 store，并展示实时加载态。后端 `PUT /api/v1/sync/conflicts/{id}/resolve` 现接收 `strategy` 字段并写入 `resolution_strategy`，完成后自动刷新列表。

### AdminOperationsView (`frontend/src/views/AdminOperationsView.vue`)
- [x] 批量用户处理指令接入后台批处理 API
- [x] 批量商品/交易/导入导出与告警模块接入真实接口
- [x] 冲突列表使用 `/sync/conflicts` 数据而非静态数组
- [x] SQL 执行器调用后端沙箱接口，并有权限/参数校验

> 2025-12-05：前端批量操作、交易清理、导入导出、冲突中心与 SQL Runner 均改为调用 `/api/v1/admin/operations/*` 与 `/api/v1/sync/conflicts` 等真实端点，支持 loading、错误提示与审计日志。

### AdminPerformanceView (`frontend/src/views/AdminPerformanceView.vue`)
- [x] 统计卡片通过 `/dashboard/stats` 等接口实时获取
- [x] “四数据库同步状态”使用 `/sync/databases/status` 真实数据
- [x] 慢查询、连接池、实时查询模块接入监控 API
- [x] `refreshAllData` 成功后刷新所有可视化组件而非仅局部
- [x] `syncDatabase`、`viewDbDetails`、`killQuery` 等按钮触发真实操作

> 2025-12-05：AdminPerformanceView 现整合 `/dashboard/stats`、`/sync/databases/status` 与 `/admin/operations/performance/insights` 数据，支持一键刷新/自动刷新、实时运行查询终止、数据库日志查看及同步触发。

### 其他后台入口
- [ ] AdminConsoleView 快捷操作（回放事件/导出冲突/AI 审核）具备真实动作或移除
- [ ] AdminProfileView 快速入口与安全建议保持与实际能力一致
- [ ] README 和 PROJECT_STATUS 章节在每次落地后同步更新

### 👤 用户中心
- [x] **个人主页** - 用户信息、在售商品、评价展示
- [x] **商品发布** - 图片上传、AI智能定价、多图预览
- [x] **消息中心** - 实时聊天、系统通知、交易提醒
- [x] **收藏夹** - 收藏商品、降价提醒

### 🔄 互动功能
- [x] **冲突处理** - 版本冲突检测、乐观锁控制、一致性校验
- [x] **同步统计** - 成功率、失败率、延迟统计、可视化图表
- [x] **冲突解决** - 手动解决冲突、自动重试机制

### ⚙️ 系统管理
- [x] **用户管理** - 用户列表、状态管理、权限控制
- [x] **数据看板** - 交易统计、用户活跃度、收入分析
- [x] **数据分析** - 图表可视化、趋势分析、报表生成
- [x] **数据表管理** - 表结构查看、数据增删改查
- [x] **系统设置** - 系统配置、参数调整
- [x] **审计日志** - 操作记录、安全审计

### 🚀 技术亮点
- [x] **四数据库异构同步** - 支持 MySQL、PostgreSQL、MariaDB、SQLite
- [x] **WebSocket 实时通信** - 实时消息推送、在线状态同步
- [x] **桌面通知集成** - 浏览器原生通知、音效提示
- [x] **高级搜索引擎** - 自动完成建议、搜索历史记录
- [x] **UI/UX 优化** - 骨架屏加载、页面过渡动画

---

## 📝 待办事项 (Todo)

- [ ] **性能优化**
  - [ ] 引入 Redis 缓存热点数据
  - [ ] 优化图片加载 (CDN/懒加载)
- [ ] **功能扩展**
  - [ ] 支付网关集成 (支付宝/微信支付沙箱)
  - [ ] 移动端适配 (PWA 或 React Native)
  - [ ] 更复杂的 AI 定价模型训练
- [ ] **运维**
  - [ ] K8s 部署配置
  - [ ] ELK 日志收集系统集成

---

## 📧 联系方式

- **项目地址：** https://github.com/lll-hhh/Campus_Trading_System
- **问题反馈：** [Issues](https://github.com/lll-hhh/Campus_Trading_System/issues)
- **功能建议：** [Discussions](https://github.com/lll-hhh/Campus_Trading_System/discussions)

---

<div align="center">

**⭐ 如果这个项目对你有帮助，请给一个 Star！⭐**

Made with ❤️ by [lll-hhh](https://github.com/lll-hhh)

</div>

---
**版本:** 2.1 | **更新:** 2025-11-19
