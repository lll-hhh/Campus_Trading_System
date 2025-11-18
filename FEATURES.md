# 校园二手交易系统 - 完整功能说明

## 📚 项目概述

本项目是一个基于多数据库同步的校园二手交易平台,支持MySQL、MariaDB、PostgreSQL、SQLite四种数据库的实时同步与一致性维护。系统采用前后端分离架构,实现了完整的用户权限管理、数据分析、智能推荐等功能。

---

## 🎯 核心功能

### 1. 多数据库同步系统 ✅

#### 1.1 数据库支持
- **MySQL 8.0**: 主数据库,REPEATABLE READ隔离级别
- **MariaDB 10.11**: 备用数据库,REPEATABLE READ隔离级别
- **PostgreSQL 15**: 读优化数据库,READ COMMITTED隔离级别
- **SQLite 3.x**: 嵌入式数据库,SERIALIZABLE隔离级别

#### 1.2 同步模式
- **实时同步**: 数据变更立即同步到所有数据库
- **周期同步**: 定时批量同步(可配置间隔)
- **混合模式**: 关键数据实时同步,其他数据周期同步
- **异步备份**: 通过Redis Streams实现事件流备份

#### 1.3 冲突处理
- **自动检测**: 版本冲突、数据不一致、约束违反
- **邮件通知**: 冲突发生时自动发送邮件给管理员
- **手动解决**: PC端界面选择数据来源进行修复
- **日志记录**: 完整的冲突记录和处理历史

### 2. 事务管理系统 ✅

#### 2.1 隔离级别配置
```python
# 针对不同数据库的最优隔离级别
MySQL/MariaDB: REPEATABLE READ  # 防止幻读
PostgreSQL: READ COMMITTED      # MVCC优化
SQLite: SERIALIZABLE           # 单写入保证
```

#### 2.2 自动重试机制
- **死锁检测**: 自动识别死锁异常
- **指数退避**: 100ms → 200ms → 400ms重试间隔
- **最大重试次数**: 可配置(默认3次)

#### 2.3 SAVEPOINT支持
- **嵌套事务**: 支持事务内部的SAVEPOINT
- **部分回滚**: 可回滚到指定保存点
- **错误恢复**: 细粒度的错误处理

### 3. 数据库程序对象 ✅

#### 3.1 触发器 (6个)
1. `trg_users_after_insert` - 用户插入后记录审计日志
2. `trg_users_after_update` - 用户更新后记录变更
3. `trg_users_after_delete` - 用户删除后记录删除日志
4. `trg_items_before_update` - 商品更新前验证价格
5. `trg_items_after_update` - 商品更新后同步版本号
6. `trg_transactions_after_update` - 交易状态变更后更新库存

#### 3.2 存储过程 (3个)
1. `sp_sync_table_data` - 表数据同步存储过程
2. `sp_calculate_user_reputation` - 计算用户信誉分
3. `sp_cleanup_old_conflicts` - 清理旧冲突记录

#### 3.3 存储函数 (3个)
1. `fn_get_user_transaction_count` - 获取用户交易次数
2. `fn_avg_price_by_category` - 按分类计算平均价格
3. `fn_check_version_conflict` - 检查版本冲突

### 4. 复杂SQL查询 ✅

#### 4.1 多表连接查询
```sql
-- 销售排行榜 (users + transactions + items + reviews 4表JOIN)
SELECT u.username, COUNT(t.id) as sales, SUM(t.total_amount) as revenue
FROM users u
LEFT JOIN transactions t ON u.id = t.seller_id
LEFT JOIN items i ON t.item_id = i.id
LEFT JOIN reviews r ON t.id = r.transaction_id
GROUP BY u.id
ORDER BY revenue DESC
```

#### 4.2 嵌套子查询
```sql
-- 价格趋势分析 (当前价格 vs 30天前价格)
SELECT 
    category_name,
    AVG(price) as current_avg,
    (SELECT AVG(price) FROM items WHERE created_at < DATE_SUB(NOW(), INTERVAL 30 DAY)) as old_avg
FROM items
GROUP BY category_id
```

#### 4.3 窗口函数与聚合
```sql
-- 用户行为分析 (按小时统计活跃度)
SELECT 
    HOUR(created_at) as hour,
    COUNT(DISTINCT buyer_id) as active_users,
    AVG(total_amount) as avg_amount
FROM transactions
WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
GROUP BY hour
```

#### 4.4 协同过滤推荐
```sql
-- 基于相似用户的商品推荐
SELECT i.* FROM items i
WHERE i.category_id IN (
    SELECT category_id FROM items WHERE id IN (
        SELECT item_id FROM transactions WHERE buyer_id IN (
            SELECT buyer_id FROM transactions WHERE item_id IN (
                SELECT item_id FROM transactions WHERE buyer_id = ?
            )
        )
    )
)
AND i.id NOT IN (SELECT item_id FROM transactions WHERE buyer_id = ?)
```

### 5. 用户权限管理 ✅

#### 5.1 RBAC模型
- **User**: 用户表
- **Role**: 角色表(管理员、教师、学生、审核员)
- **Permission**: 权限表(用户管理、商品发布、订单管理等)
- **UserRole**: 用户-角色关联表
- **RolePermission**: 角色-权限关联表

#### 5.2 权限控制
- **路由守卫**: 前端路由权限验证
- **API鉴权**: 后端接口权限验证
- **数据过滤**: 基于权限的数据可见性控制

### 6. 数据备份与恢复 ✅

#### 6.1 自动备份脚本
```bash
# 执行备份
./scripts/backup.sh

# 功能:
- 备份4个数据库到独立文件
- 自动压缩备份文件
- 验证备份完整性
- 清理30天前的旧备份
- 邮件通知备份结果
```

#### 6.2 恢复脚本
```bash
# 执行恢复
./scripts/restore.sh

# 功能:
- 交互式选择备份文件
- 恢复前确认提示
- 自动创建当前数据库备份
- 验证恢复结果
```

### 7. 前端可视化 ✅

#### 7.1 图表组件 (ECharts)
1. **SyncTrendChart** - 同步趋势折线图
   - 同步成功数、冲突数、AI请求数
   - 支持区域缩放、数据导出
   
2. **ConflictPieChart** - 冲突类型饼图
   - 版本冲突、数据不一致、约束违反
   - 环形图展示,支持高亮

3. **DatabaseStatusChart** - 数据库状态柱状图
   - 连接数、同步延迟、错误率
   - 双Y轴展示

4. **HeatmapChart** - 活动热力图
   - 24小时x7天的同步活动分布
   - 颜色深浅表示活跃度

#### 7.2 页面模块
1. **DashboardView** - 数据仪表盘
   - 关键指标卡片
   - 同步状态监控
   - 最近7天统计

2. **AnalyticsView** - 数据分析中心
   - 多维度图表展示
   - 销售排行榜
   - 分类销售分析

3. **MarketSearchView** - 市场搜索
   - 高级搜索功能
   - 多条件筛选
   - 智能推荐

4. **AdminConsoleView** - 管理控制台
   - 冲突解决界面
   - 同步日志查看

5. **UserManagementView** - 用户管理
   - 用户列表
   - 角色分配
   - 权限矩阵

6. **SystemSettingsView** - 系统设置
   - 数据库连接配置
   - 同步策略设置
   - 邮件通知配置
   - 性能优化选项

7. **ProfileCenterView** - 个人中心
   - 用户信息
   - 交易历史
   - 收藏夹

---

## 📊 数据库表结构

### 核心业务表 (34张)

#### 用户模块 (6张)
- `users` - 用户表
- `user_profiles` - 用户资料
- `roles` - 角色表
- `permissions` - 权限表
- `user_roles` - 用户角色关联
- `role_permissions` - 角色权限关联

#### 商品模块 (8张)
- `categories` - 商品分类
- `items` - 商品表
- `item_media` - 商品图片/视频
- `item_attachments` - 商品附件
- `favorites` - 收藏表
- `follows` - 关注表
- `comments` - 评论表
- `tags` - 标签表
- `item_tags` - 商品标签关联

#### 交易模块 (6张)
- `offers` - 报价表
- `transactions` - 交易表
- `transaction_logs` - 交易日志
- `payments` - 支付表
- `deliveries` - 配送表
- `reviews` - 评价表

#### AI模块 (5张)
- `ai_chats` - AI对话
- `ai_actions` - AI操作记录
- `ai_models` - AI模型配置
- `ai_insights` - AI洞察
- `fraud_patterns` - 欺诈模式

#### 运营模块 (5张)
- `reports` - 举报表
- `moderation_tasks` - 审核任务
- `blacklists` - 黑名单
- `audit_logs` - 审计日志
- `config_items` - 配置项

#### 同步模块 (4张)
- `sync_configs` - 同步配置
- `sync_logs` - 同步日志
- `conflict_records` - 冲突记录
- `daily_stats` - 每日统计

---

## 🚀 技术栈

### 后端
- **框架**: FastAPI 0.110+
- **ORM**: SQLAlchemy 2.0
- **数据库**: MySQL 8.0, MariaDB 10.11, PostgreSQL 15, SQLite 3.x
- **缓存**: Redis 7.0
- **任务队列**: APScheduler
- **认证**: JWT + OAuth2
- **日志**: Loguru

### 前端
- **框架**: Vue 3.4 + TypeScript
- **UI库**: Naive UI + UnoCSS
- **图表**: ECharts 5.5
- **路由**: Vue Router 4.3
- **状态管理**: Pinia 2.1
- **HTTP客户端**: Axios 1.6

### 数据库特性
- **连接池**: 每个数据库独立连接池(10+20配置)
- **事务隔离**: 针对不同数据库优化
- **索引优化**: 复合索引、全文索引
- **分区表**: 交易表按年份分区

---

## 📁 项目结构

```
Campus_Trading_System/
├── backend/                    # 后端代码
│   ├── apps/
│   │   ├── api_gateway/       # API网关
│   │   │   ├── routers/       # 路由模块
│   │   │   │   ├── analytics.py      # 分析API (复杂SQL)
│   │   │   │   ├── auth.py            # 认证API
│   │   │   │   ├── dashboard.py       # 仪表盘API
│   │   │   │   ├── database.py        # 数据库管理API
│   │   │   │   ├── market.py          # 市场搜索API
│   │   │   │   └── sync.py            # 同步管理API
│   │   │   └── main.py        # 主入口
│   │   ├── core/              # 核心模块
│   │   │   ├── models/        # ORM模型 (34个表)
│   │   │   ├── config.py      # 配置管理
│   │   │   ├── database.py    # 数据库连接
│   │   │   ├── security.py    # 安全认证
│   │   │   ├── transaction.py # 事务管理 ⭐
│   │   │   ├── sync_engine.py # 同步引擎 ⭐
│   │   │   └── sync_payloads.py # 同步负载
│   │   ├── services/          # 服务层
│   │   │   ├── db_operations.py  # 统一数据库操作 ⭐
│   │   │   ├── ai_pricing.py     # AI定价
│   │   │   ├── notifications.py  # 邮件通知
│   │   │   └── db_initializer.py # 数据库初始化
│   │   ├── inventory_service/ # 库存服务 (四库同步)
│   │   ├── trade_service/     # 交易服务 (四库同步)
│   │   ├── ai_service/        # AI服务
│   │   ├── sync_service/      # 同步服务
│   │   └── monitoring_service/ # 监控服务
│   ├── sql/                   # SQL脚本
│   │   ├── mysql_schema.sql   # MySQL建表+触发器+存储过程 ⭐
│   │   ├── mariadb_schema.sql # MariaDB建表脚本
│   │   ├── postgres_schema.sql # PostgreSQL建表脚本
│   │   └── sqlite_schema.sql  # SQLite建表脚本
│   ├── docs/                  # 文档
│   │   ├── transaction-management.md        # 事务管理文档 ⭐
│   │   ├── 4-DATABASE-SYNC.md              # 四库同步文档 ⭐
│   │   ├── TRANSACTION_SUMMARY.md          # 功能总结
│   │   └── SYNC_AND_TRANSACTION_COMPLETE.md # 完成总结
│   └── alembic/               # 数据库迁移
├── frontend/                  # 前端代码
│   ├── src/
│   │   ├── views/             # 页面组件 (7个)
│   │   │   ├── DashboardView.vue         # 数据仪表盘
│   │   │   ├── AnalyticsView.vue         # 数据分析 ⭐
│   │   │   ├── MarketSearchView.vue      # 市场搜索
│   │   │   ├── AdminConsoleView.vue      # 管理控制台
│   │   │   ├── UserManagementView.vue    # 用户管理 ⭐
│   │   │   ├── SystemSettingsView.vue    # 系统设置 ⭐
│   │   │   └── ProfileCenterView.vue     # 个人中心
│   │   ├── components/        # 组件
│   │   │   ├── charts/        # 图表组件 ⭐
│   │   │   │   ├── SyncTrendChart.vue      # 同步趋势图
│   │   │   │   ├── ConflictPieChart.vue    # 冲突饼图
│   │   │   │   ├── DatabaseStatusChart.vue # 数据库状态图
│   │   │   │   └── HeatmapChart.vue        # 热力图
│   │   │   ├── AdvancedSearchPanel.vue
│   │   │   ├── AIChatBox.vue
│   │   │   └── ConflictTable.vue
│   │   ├── stores/            # Pinia状态管理
│   │   └── router/            # 路由配置
│   └── package.json
├── scripts/                   # 脚本
│   ├── backup.sh              # 备份脚本 ⭐
│   └── restore.sh             # 恢复脚本 ⭐
├── docker-compose.yml         # Docker编排
└── README.md

⭐ = 本次新增/重点功能
```

---

## 🔧 部署与运行

### 1. 启动数据库
```bash
docker-compose up -d
```

### 2. 初始化数据库
```bash
cd backend
python -m alembic upgrade head
```

### 3. 启动后端
```bash
cd backend
uvicorn apps.api_gateway.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. 启动前端
```bash
cd frontend
npm install
npm run dev
```

### 5. 访问系统
- 前端: http://localhost:5173
- 后端API: http://localhost:8000
- API文档: http://localhost:8000/docs

---

## 📈 性能优化

### 1. 数据库优化
- **连接池**: 预分配连接,避免频繁创建
- **索引**: 为常用查询字段建立复合索引
- **分区表**: 大表按时间分区,提升查询速度
- **查询缓存**: Redis缓存热点数据

### 2. 同步优化
- **批量操作**: 使用bulk_insert减少网络往返
- **异步备份**: Redis Streams实现异步事件流
- **冲突检测**: 版本号机制减少锁竞争

### 3. 前端优化
- **代码分割**: 路由级别懒加载
- **虚拟滚动**: 大列表性能优化
- **图表优化**: ECharts按需引入

---

## 🎓 技术亮点

1. **多数据库一致性**: 实现4种数据库的强一致性同步
2. **事务管理**: 完整的ACID保证+死锁处理+自动重试
3. **复杂SQL**: 6种复杂SQL查询模式(JOIN/子查询/窗口函数/协同过滤)
4. **数据库编程**: 触发器+存储过程+存储函数完整实现
5. **可视化**: ECharts实现4种图表类型
6. **权限管理**: RBAC模型完整实现
7. **备份恢复**: 生产级备份脚本+验证机制
8. **响应式UI**: 移动端/PC端自适应

---

## 📝 答辩要点

### 1. 技术难点
- Q: 如何保证4个数据库的数据一致性?
- A: 采用两阶段提交+版本号机制+冲突检测,实时同步+Redis Streams异步备份

### 2. 复杂SQL
- Q: 展示一个复杂的SQL查询
- A: 演示销售排行榜(4表JOIN+聚合+子查询+时间范围)

### 3. 性能优化
- Q: 如何处理高并发?
- A: 连接池+索引优化+缓存+异步处理+数据库分区

### 4. 安全性
- Q: 如何保证系统安全?
- A: JWT认证+RBAC权限+SQL注入防护+XSS防护+HTTPS

---

## 👥 联系方式

- 作者: [Your Name]
- 邮箱: [Your Email]
- GitHub: https://github.com/lll-hhh/Campus_Trading_System

---

**文档更新时间**: 2025-01-18
**系统版本**: v1.0.0
