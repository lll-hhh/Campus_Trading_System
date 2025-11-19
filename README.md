# 🎓 校园二手交易系统
# Campus Trading System

<div align="center">

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/Python-3.10+-green.svg)
![Vue](https://img.shields.io/badge/Vue-3.4-brightgreen.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-teal.svg)
![Status](https://img.shields.io/badge/Status-95%25%20Complete-yellow.svg)

基于 FastAPI + Vue3 + TypeScript 的现代化校园二手交易平台

**特色：四数据库异构同步 • WebSocket实时通知 • AI智能定价**

[功能特性](#-功能特性) • [快速开始](#-快速开始) • [部署指南](#-部署指南) • [开发文档](#-开发文档)

</div>

---

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
- [贡献指南](#-贡献指南)
- [许可证](#-许可证)

---

## ✨ 功能特性

### 🛍️ 用户端 - 淘宝风格交易市场

#### 商品浏览与搜索
- 📱 **商品市场** - 8大分类、网格/列表双视图、智能分页
- 🔍 **智能搜索** - 实时搜索建议、搜索历史、高级筛选
- 🏷️ **多维筛选** - 价格区间、成色筛选、5种排序方式
- 📊 **搜索结果** - 关键词高亮、相关度排序、筛选面板

#### 商品交易
- 🖼️ **商品详情** - 多图轮播、详细描述、卖家评分、标签系统
- 💬 **评论互动** - 发表评论、楼中楼回复、买卖沟通
- 📝 **商品发布** - 多图上传、智能分类、标签管理、编辑功能
- 🤝 **交易流程** - 在线下单、联系卖家、线下交易、确认收货

#### 个人中心
- 📦 **我的商品** - 在售中/已售出/已下架状态管理
- 💰 **交易记录** - 我买到的/我卖出的订单追踪
- 💬 **消息中心** - 实时聊天、会话管理、未读提示
- 🔔 **通知中心** - 实时通知、桌面提醒、音效提示
- 👤 **个人主页** - 用户信息、在售商品、评价展示
- ⚙️ **账号设置** - 资料修改、密码更改、隐私设置

#### 互动功能
- ⭐ **收藏系统** - 收藏商品、收藏列表管理
- 🛒 **购物车** - 批量加购、快速下单
- 🚨 **举报功能** - 违规举报、内容审核

### 🔧 管理员端 - 系统监控与管理

#### 数据库同步监控 ⭐核心特色
- 📊 **同步状态监控** - MySQL/PostgreSQL/MariaDB/SQLite 实时同步
- 🔄 **冲突处理** - 版本冲突检测、乐观锁控制、一致性校验
- 📈 **同步统计** - 成功率、失败率、延迟统计、可视化图表
- 🎯 **冲突解决** - 手动解决冲突、自动重试机制

#### 系统管理
- 👥 **用户管理** - 用户列表、状态管理、权限控制
- 📊 **数据看板** - 交易统计、用户活跃度、收入分析
- 📈 **数据分析** - 图表可视化、趋势分析、报表生成
- 🗃️ **数据表管理** - 表结构查看、数据增删改查
- ⚙️ **系统设置** - 系统配置、参数调整
- 📝 **审计日志** - 操作记录、安全审计

### 🚀 技术亮点

1. **四数据库异构同步** ⭐
   - 支持 MySQL、PostgreSQL、MariaDB、SQLite 四种数据库
   - 基于乐观锁的并发控制（版本号机制）
   - 实时冲突检测和处理
   - 数据一致性保证

2. **WebSocket 实时通信**
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
- **PostgreSQL** 15+ - 同步数据库
- **MariaDB** 10+ - 同步数据库
- **SQLite** 3+ - 同步数据库

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
│   │   │   ├── SyncMonitorView.vue    # 同步监控
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
docker-compose up -d

# 3. 查看服务状态
docker-compose ps

# 4. 访问系统
# 前端: http://localhost:5174
# API文档: http://localhost:8001/docs
# 管理员账号: admin / admin123
# 普通用户: user1 / password123
```

服务说明：
- **frontend** - 前端服务（端口 5174）
- **backend** - 后端API（端口 8001）
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
uvicorn apps.api_gateway.main:app --reload --host 0.0.0.0 --port 8001
```

#### 前端启动

```bash
# 1. 进入前端目录
cd frontend

# 2. 安装依赖
npm install

# 3. 启动开发服务器
npm run dev

# 4. 访问系统
# http://localhost:5174
```

### 方式三：生产环境部署

详见 [部署指南](#-部署指南) 章节

---

## ⚙️ 环境配置

### 后端环境变量 (.env)

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
CORS_ORIGINS=["http://localhost:5174","http://localhost:3000"]

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
VITE_API_BASE_URL=http://localhost:8001
VITE_WS_BASE_URL=ws://localhost:8001

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
docker-compose build

# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 查看服务状态
docker-compose ps
```

#### 3. 初始化数据库

```bash
# 进入后端容器
docker-compose exec backend bash

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
        proxy_pass http://localhost:5174;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # API
    location /api {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # WebSocket
    location /api/v1/ws {
        proxy_pass http://localhost:8001;
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
Type=simple
User=www-data
WorkingDirectory=/var/www/campus-trading/backend
Environment="PATH=/var/www/campus-trading/backend/venv/bin"
ExecStart=/var/www/campus-trading/backend/venv/bin/uvicorn apps.api_gateway.main:app --host 0.0.0.0 --port 8001 --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# 启动服务
sudo systemctl daemon-reload
sudo systemctl start campus-trading-backend
sudo systemctl enable campus-trading-backend
sudo systemctl status campus-trading-backend
```

#### 2. 前端部署

```bash
cd /var/www/campus-trading/frontend

# 安装Node.js 18+
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
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /api/v1/ws {
        proxy_pass http://127.0.0.1:8001;
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

启动后端服务后，访问：

- **Swagger UI:** http://localhost:8001/docs
- **ReDoc:** http://localhost:8001/redoc

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
<summary><b>数据库同步相关</b></summary>

- `GET /api/v1/sync/status` - 获取同步状态
- `POST /api/v1/sync/start` - 启动同步
- `POST /api/v1/sync/stop` - 停止同步
- `GET /api/v1/sync/conflicts` - 获取冲突列表
- `POST /api/v1/sync/conflicts/{id}/resolve` - 解决冲突
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
    allow_origins=["http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 3. WebSocket连接失败

**问题：** WebSocket连接无法建立

**解决：**
```typescript
// 检查WebSocket URL是否正确
const ws = new WebSocket('ws://localhost:8001/api/v1/ws/notifications/1')

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

**问题：** `docker-compose up` 失败

**解决：**
```bash
# 查看详细日志
docker-compose logs backend
docker-compose logs frontend

# 重新构建
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# 检查端口占用
sudo lsof -i :8001
sudo lsof -i :5174
```

---

## 📊 项目状态

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
**版本:** 2.0 | **更新:** 2025-11-18
