# CampuSwap 校园智能二手交易平台——需求与技术选型

## 1. 背景与建设目标
CampuSwap 面向校园内二手物品流通痛点，要求在多数据库并行部署的前提下，构建具备实时/周期同步、权限管控、可视化报表与轻量 AI 辅助的全链路平台。系统需完全满足《数据库系统实践》任务书 1-6 条要求，并额外落实 Code Agent 规范中的 34 张核心数据表与四库同步机制。

## 2. 角色模型与核心业务流程
| 角色 | 主要职责 | 关键功能 |
| --- | --- | --- |
| 管理员 | 平台配置、审核、风控与同步监控 | 数据库同步策略配置、冲突修复、黑名单、报表导出 |
| 学生卖家 | 发布闲置、管理订单 | 物品发布、价格建议、物流跟踪、聊天沟通 |
| 学生买家 | 浏览、收藏、下单、支付 | 语义搜索、AI 风险提示、订单管理、评价 |
| 风控/运营人员 | 监控异常、策略迭代 | AI 决策解释、异常报表、配置模板 |

主流程：注册登录 → 个人认证 → 发布/浏览商品 → 生成报价 → 下单与履约 → 多库同步 → 报表与监控 → 冲突修复与审计。

## 3. 需求总览
### 3.1 功能需求
1. **多数据库同步**：MySQL8、PostgreSQL14、MariaDB10.6、SQLite3.35 同步，表结构 34 张统一；实时（事件驱动）+ 周期任务。
2. **交易闭环**：分类、发布、收藏、报价、订单、支付、配送、评价全流程，含日志与审核。
3. **权限管理**：RBAC 模型（users/roles/permissions/...），支持精细化 API 与数据权限。
4. **AI 能力**：定价建议（KNN）、风险识别（规则+特征）、语义搜索（关键词映射 + BM25）。所有 AI 操作写入 ai_actions 并可追溯。
5. **同步冲突处理**：乐观锁 `sync_version` 检测，写 conflict_records，触发邮件；PC 端提供修复界面，移动端展示日报/异常报表。
6. **前端体验**：Vue3 + TypeScript + Vite，自适应、深浅主题、移动仪表盘；提供管理后台、学生活动端、移动报告端。
7. **报表统计**：daily_stats、sync_logs、fraud_patterns 等数据驱动的折线/柱状/饼图，支持导出。
8. **工程交付**：完整文档、数据库脚本、Docker Compose、源代码、运行说明与演示材料。

### 3.2 非功能需求
- **性能**：单节点 1k QPS，中位响应 < 200ms；定时同步窗口 < 5 分钟。
- **可靠性**：同步失败自动重试 ≥3 次，冲突 1 分钟内通知；数据库备份每日 + 每周全量。
- **安全**：HTTPS、JWT、RLS（按角色过滤）、操作审计；敏感字段加密；最小权限访问数据库。
- **可维护性**：微服务拆分、接口契约（OpenAPI + AsyncAPI）、CI lint/test 覆盖、IaC 化部署。
- **可扩展性**：支持新增数据库类型或 AI 模块，服务无共享状态，依赖 Redis、消息队列解除耦合。

## 4. 技术选型
### 4.1 总体架构
- **模式**：前后端分离 + Python 微服务（FastAPI）+ 事件驱动同步（Redis 队列）+ 数据抽象层（SQLAlchemy ORM + Alembic 管理 schema）。
- **部署**：Docker Compose（本地）/Kubernetes（扩展），统一配置中心（config_items 表+环境变量）。

### 4.2 后端
| 组件 | 选型 | 理由 |
| --- | --- | --- |
| Web 框架 | FastAPI 0.110+ | ASGI、高性能、内置 OpenAPI、适配微服务 |
| ORM | SQLAlchemy 2.x + Pydantic v2 | 多数据库方言支持、类型安全、数据验证 |
| 消息队列 | Redis Streams | 轻量、可持久化、便于同步事件队列 |
| 任务调度 | APScheduler + FastAPI BackgroundTasks | 支持周期同步、报表生成 |
| 微服务拆分 | `gateway`, `inventory`, `trade`, `sync`, `ai`, `monitoring` | 对应业务域，方便独立扩展与部署 |
| 测试 | Pytest + HTTPX | 异步客户端测试 API，易于集成 CI |
| 代码规范 | black, flake8, mypy, isort, pre-commit | 满足 Google Python 风格与静态检查 |

### 4.3 前端
| 组件 | 选型 | 理由 |
| --- | --- | --- |
| 框架 | Vue 3.4 + Vite 5 + TypeScript 5 | 轻量、现代、支持组合式 API |
| 状态管理 | Pinia | 类型友好、与 Vue3 深度集成 |
| UI 库 | Naive UI + UnoCSS | 自定义主题、移动端友好 |
| 路由 | Vue Router 4 | 动态路由、权限守卫 |
| 可视化 | ECharts 5 | 丰富报表图形 |
| Lint | ESLint + @typescript-eslint + Prettier | 满足 Google JS/TS 风格 |

### 4.4 数据库与同步
- **主存储**：MySQL 8 作为写前数据库，其余三库订阅同步。
- **同步流程**：
  1. SQLAlchemy 事件监听 insert/update/delete → 将变更记录序列化（payload + sync_version）写入 Redis Stream。
  2. `sync_worker` 消费事件，按目标数据库连接串分发，写操作时携带 `WHERE sync_version = ?` 乐观锁。
  3. 若影响行数 0 → 记录 conflict_records，发邮件 + WebSocket 提醒；管理员通过 `/admin/conflicts` 解决。
  4. APScheduler 定时任务根据 `sync_configs` 回放未完成事件，生成 `daily_stats`、`sync_logs`。

### 4.5 AI 模块
- **定价建议**：kNN（scikit-learn），基于品类、品牌、使用时长、历史成交价；模型文件存放 `ai_models` 表 + MinIO/本地。
- **风险识别**：fraud_patterns.rule_json 维护规则（关键词、频次、异常支付），在 `ai_actions` 留痕。
- **语义搜索**：TF-IDF + 关键词扩展，支持多字段匹配，结果写入 `ai_insights`。

## 5. 数据库结构映射
- **通用字段**：`id BIGINT PK`, `created_at`, `updated_at`, `sync_version INT`。
- **分组**：
  1. 用户与权限：users, user_profiles, roles, permissions, role_permissions, user_roles
  2. 商品与内容：categories, items, item_medias, item_attachments, favorites, follows, comments, tags
  3. 交易与履约：offers, transactions, transaction_logs, payments, deliveries, reviews
  4. AI 与智能服务：ai_chats, ai_actions, ai_models, ai_insights, fraud_patterns
  5. 风控与运营：reports, moderation_tasks, blacklists, audit_logs, config_items
  6. 同步与监控：sync_configs, sync_logs, conflict_records, daily_stats
- **规范化**：所有表满足 3NF；关键查询添加复合索引（如 `items(category_id, status)`、`transactions(buyer_id, status)`）。
- **分区策略**：大体量表（transactions, sync_logs）按时间分区；SQLite 版本采用视图 + 轻量触发器保持接口一致。

## 6. 接口与模块边界
| 微服务 | 端口 | 主要职责 | 对外接口示例 |
| --- | --- | --- | --- |
| API Gateway | 8000 | 统一入口、鉴权、路由 | `/api/v1/*`, `/auth/login`, `/admin/conflicts` |
| Inventory Service | 8010 | 分类、物品、收藏、评论 | `/inventory/items`, `/inventory/tags` |
| Trade Service | 8020 | 报价、交易、支付、配送 | `/trade/offers`, `/trade/transactions/{id}` |
| Sync Service | 8030 | 多库写入、冲突检测、统计 | `/sync/status`, `/sync/configs` |
| AI Service | 8040 | 定价、风险、语义搜索 | `/ai/pricing`, `/ai/insights/search` |
| Monitoring Service | 8050 | 报表、告警、健康检查 | `/monitoring/daily-stats`, `/monitoring/alerts` |

所有服务通过 gRPC/REST 内部调用（本阶段先使用 REST + 内网 token），对外统一经过 Gateway。

## 7. 安全与合规
- OAuth2 + JWT + Refresh Token；管理端支持 MFA。
- 数据脱敏：手机号、邮箱、支付信息使用 KMS 加密；操作写入 audit_logs。
- 日志：结构化 JSON，统一推送到 Loki/ELK。
- 备份：mysqldump/pg_dump/mariabackup/SQLite 文件快照，存 OSS；定期演练恢复。

## 8. 交付物与阶段计划
| 阶段 | 交付 | 验收点 |
| --- | --- | --- |
| P0 需求&选型 | 本文档、34 张表 E-R 草图、任务书确认 | 评审通过 |
| P1 架构底座 | Docker Compose、后端/前端脚手架、CI 配置 | `docker compose up` 可跑空白系统 |
| P2 功能增量 | 多库同步内核、AI 服务 MVP、前端主流程 | Demo 可展示 |
| P3 验证与文档 | 测试报告、运行手册、答辩 PPT | 满足评分标准 |

## 9. 风险与对策
- **多库一致性复杂**：通过事件溯源 + 乐观锁 + 冲突工单降低风险。
- **AI 数据不足**：设计模拟/冷启动策略，允许手工标注 + 结合规则。
- **时间紧**：优先实现核心同步、交易闭环与权限，AI/移动报表迭代推进。

---
该文档将指导后续环境搭建、代码落地与答辩材料编写。