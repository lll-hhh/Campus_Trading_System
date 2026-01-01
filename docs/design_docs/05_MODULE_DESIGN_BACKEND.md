# 凤凰汽配管理系统 - 后端模块设计文档

## 1. 模块划分
后端基于 FastAPI 框架，采用分层架构设计，主要分为以下核心模块：

### 1.1 核心基础模块 (Core Module)
- **功能**：提供系统级的基础设施，包括配置管理、日志记录、异常处理、数据库连接池。
- **设计要点**：
  - 使用 Pydantic 设置全局配置类 `Settings`。
  - 封装统一的日志装饰器，记录每个 API 的入参、出参及执行时间。
  - 实现自定义 `AppException`，支持业务错误码。

### 1.2 认证与授权模块 (Auth Module)
- **功能**：用户注册、登录、Token 签发与校验、RBAC 权限控制。
- **设计要点**：
  - **JWT 机制**：使用 `python-jose` 生成 Access Token，有效期 24 小时。
  - **密码安全**：使用 `passlib` 的 `argon2` 算法进行哈希。
  - **权限依赖**：利用 FastAPI 的 `Depends` 机制实现细粒度的权限校验，例如 `@requires_permission("part:delete")`。

### 1.3 零件与分类模块 (Part Module)
- **功能**：零件的 CRUD、多级分类树构建、兼容性查询。
- **设计要点**：
  - **递归分类**：使用递归算法构建分类树，支持无限级分类。
  - **搜索优化**：集成 SQLAlchemy 的 `match` 函数实现全文检索。
  - **图片处理**：集成 `Pillow` 库，在上传零件图片时自动压缩并生成 WebP 格式以节省带宽。

### 1.4 库存管理模块 (Inventory Module)
- **功能**：入库、出库、库存锁定、预警计算。
- **设计要点**：
  - **事务控制**：在出库操作中，使用数据库事务确保“扣减库存”与“生成出库单”的原子性。
  - **并发处理**：使用 `SELECT ... FOR UPDATE` 悲观锁防止超卖现象。
  - **预警逻辑**：后台定时任务（Celery）每小时扫描一次库存，发现低于 `min_stock` 的零件即向管理员推送通知。

### 1.5 交易与订单模块 (Trade Module)
- **功能**：采购车管理、订单状态机流转。
- **设计要点**：
  - **状态机设计**：定义严格的订单状态流转规则（如：只有 `paid` 状态才能变为 `shipped`）。
  - **订单号生成**：采用“时间戳 + 机器 ID + 随机序列”算法，确保分布式环境下的唯一性。

### 1.6 AI 智能服务模块 (AI Module)
- **功能**：自然语言处理、零件推荐、智能问答。
- **设计要点**：
  - **流式响应**：支持 Server-Sent Events (SSE)，实现 AI 回复的逐字显示。
  - **上下文管理**：在 Redis 中存储用户的对话上下文，实现多轮对话。
  - **Prompt 工程**：针对汽配业务优化 Prompt，确保 AI 能够准确识别 OEM 码和车型信息。

## 2. 核心算法说明

### 2.1 零件兼容性匹配算法
当用户搜索特定车型（如“2020款 丰田 凯美瑞”）时，系统执行以下逻辑：
1. **关键词提取**：从搜索词中提取品牌、车系、年份。
2. **倒排索引查询**：在 `parts.compatibility` 字段中进行模糊匹配。
3. **权重排序**：根据匹配度（品牌匹配 > 车系匹配 > 年份匹配）对结果进行打分排序。

### 2.2 库存锁定算法 (Inventory Locking)
为了防止用户在下单过程中库存被他人抢占：
1. 用户点击“提交订单”。
2. 系统开启事务。
3. 执行 `UPDATE inventories SET quantity = quantity - :qty WHERE part_id = :pid AND quantity >= :qty`。
4. 如果更新行数为 0，抛出“库存不足”异常。
5. 如果更新成功，创建订单并提交事务。
6. 若订单在 30 分钟内未支付，触发定时任务释放库存。

## 3. 接口设计规范
- **URL 风格**：遵循 RESTful 规范，如 `GET /api/v1/parts/{id}`。
- **请求格式**：统一使用 `application/json`。
- **响应结构**：
  ```json
  {
    "success": true,
    "data": { ... },
    "message": "操作成功",
    "timestamp": 1672531200
  }
  ```

## 4. 安全设计

### 4.1 输入校验
所有 API 入参均通过 Pydantic 模型进行严格校验，防止 SQL 注入和 XSS 攻击。

### 4.2 频率限制 (Rate Limiting)
使用 Redis 记录每个 IP 的请求频率：
- 登录接口：每分钟最多 5 次。
- 搜索接口：每分钟最多 60 次。
- 超过限制返回 `429 Too Many Requests`。

### 4.3 数据脱敏
在返回用户信息时，自动过滤 `hashed_password` 字段；在返回订单信息时，对手机号进行星号脱敏处理。

## 5. 性能优化策略
1. **异步数据库驱动**：使用 `aiomysql` 配合 SQLAlchemy 2.0，实现全链路异步。
2. **二级缓存**：
   - 一级缓存：SQLAlchemy Session 缓存。
   - 二级缓存：Redis 缓存热点零件数据。
3. **Gzip 压缩**：后端开启 Gzip 压缩，减少 JSON 数据传输体积。

## 6. 代码规范与开发流程 (Development Standards)

### 6.1 Python 代码规范
- **遵循 PEP 8**：使用 `ruff` 进行自动格式化和静态检查。
- **类型提示**：所有函数定义必须包含类型注解（Type Hints）。
- **命名约定**：
  - 类名：`PascalCase`
  - 函数/变量名：`snake_case`
  - 常量：`UPPER_SNAKE_CASE`
- **注释要求**：复杂的业务逻辑必须编写 Docstring，说明参数、返回值和异常。

### 5.2 异常处理规范
- **自定义异常**：继承 `AppException`，定义统一的错误码。
- **捕获范围**：严禁使用空的 `except: pass`，必须捕获具体异常并记录日志。
- **返回格式**：所有异常最终由全局异常处理器捕获，返回统一的 JSON 格式。

### 5.3 数据库操作规范
- **Session 管理**：使用 `Depends(get_db)` 注入数据库会话，确保请求结束自动关闭。
- **事务控制**：涉及多表更新的操作必须使用 `with db.begin():` 确保原子性。
- **查询优化**：避免在循环中执行数据库查询（N+1 问题），优先使用 `joinedload`。

### 5.4 Git 提交规范
- **格式**：`<type>(<scope>): <subject>`
- **类型**：
  - `feat`: 新功能
  - `fix`: 修复 Bug
  - `docs`: 文档更新
  - `refactor`: 代码重构
  - `test`: 测试用例
- **分支管理**：`main` 为稳定分支，`develop` 为开发分支，功能开发使用 `feature/*` 分支。

## 7. 核心业务逻辑流程图 (Logic Flows)

### 5.1 订单创建逻辑
1. 校验用户权限。
2. 校验采购车零件库存是否充足。
3. 开启数据库事务。
4. 扣减库存（行级锁防止超卖）。
5. 创建订单记录。
6. 创建订单详情记录。
7. 记录库存变动日志。
8. 提交事务。
9. 异步发送通知。

### 5.2 库存盘点逻辑
1. 生成盘点快照（记录当前账面库存）。
2. 录入实盘数据。
3. 计算差异（盈亏）。
4. 审核差异。
5. 更新库存余额。
6. 生成财务调整凭证。

## 8. 性能优化实践
- **缓存策略**：对高频访问的零件分类、供应商列表使用 Redis 缓存，设置 1 小时过期。
- **异步任务**：使用 `BackgroundTasks` 处理邮件发送、报表生成等耗时操作。
- **索引优化**：针对搜索频率高的 `oem_no`、`name` 字段建立复合索引。

## 9. 核心服务层实现细节 (Service Layer)

### 5.1 零件服务 (`PartService`)
- **`get_part_by_oem(oem_no)`**:
  - 逻辑：先查 Redis 缓存，未命中则查数据库，并回填缓存。
- **`update_part_stock(part_id, delta)`**:
  - 逻辑：使用 `SELECT FOR UPDATE` 锁定行，计算新库存，更新并记录日志。

### 5.2 订单服务 (`OrderService`)
- **`create_order(user_id, items)`**:
  - 逻辑：
    1. 开启事务。
    2. 校验所有零件库存。
    3. 扣减库存。
    4. 生成订单号。
    5. 保存订单及详情。
    6. 提交事务。
- **`cancel_order(order_id)`**:
  - 逻辑：校验订单状态，回滚库存，更新订单状态。

### 5.3 AI 服务 (`AIService`)
- **`recognize_part_image(image_data)`**:
  - 逻辑：
    1. 图像预处理（缩放、归一化）。
    2. 调用深度学习模型接口。
    3. 解析模型输出，匹配数据库零件。
    4. 返回识别结果及置信度。

## 10. 后端中间件设计 (Middleware)

### 5.1 认证中间件 (`AuthMiddleware`)
- **功能**：解析 Header 中的 JWT Token，校验合法性，并将用户信息注入 `request.state`。

### 5.2 日志中间件 (`LoggingMiddleware`)
- **功能**：记录每个请求的 URL、方法、耗时、状态码，对于 4xx/5xx 错误记录请求体。

### 5.3 限流中间件 (`RateLimitMiddleware`)
- **功能**：基于 Redis 的令牌桶算法，限制每个 IP 的每秒请求数。

## 11. 异步任务处理 (Celery/BackgroundTasks)
- **报表导出**：对于大数据量的 Excel 导出，采用异步处理，完成后通过 WebSocket 通知用户下载。
- **邮件发送**：注册成功、订单发货等通知采用异步发送，避免阻塞主流程。
- **定时任务**：
  - 每日凌晨自动清理过期 Token。
  - 每小时同步一次库存预警状态。

## 12. 后端单元测试示例
```python
def test_create_order_success(db_session):
    # 准备数据
    part = create_test_part(db_session, stock=10)
    # 执行操作
    order = OrderService.create_order(user_id=1, items=[{"part_id": part.id, "quantity": 5}])
    # 验证结果
    assert order.status == "pending"
    assert part.stock == 5

def test_create_order_insufficient_stock(db_session):
    part = create_test_part(db_session, stock=2)
    with pytest.raises(InsufficientStockException):
        OrderService.create_order(user_id=1, items=[{"part_id": part.id, "quantity": 5}])
```

## 13. 核心业务逻辑深度解析 (Business Logic)

### 5.1 零件搜索算法
- **多维度匹配**：支持按 `name`, `oem_no`, `brand`, `compatible_models` 进行全文检索。
- **权重排序**：
  1. OEM 编号精确匹配 (权重 100)。
  2. 名称精确匹配 (权重 80)。
  3. 名称模糊匹配 (权重 50)。
  4. 适用车型匹配 (权重 30)。
- **性能优化**：使用 SQLAlchemy 的 `or_` 和 `ilike` 构造查询，并对高频搜索词进行 Redis 缓存。

### 5.2 库存锁定与释放机制
- **锁定场景**：用户提交订单但未支付。
- **实现方式**：
  1. 在 `inventory` 表中增加 `locked_quantity` 字段。
  2. 提交订单时：`quantity -= order_qty`, `locked_quantity += order_qty`。
  3. 支付成功：`locked_quantity -= order_qty`。
  4. 订单取消/超时：`quantity += order_qty`, `locked_quantity -= order_qty`。
- **一致性保证**：所有操作封装在数据库事务中，并使用行级锁。

### 5.3 报表异步生成流程
1. 用户发起报表导出请求。
2. 后端生成一个唯一的 `task_id` 并返回给前端。
3. 后端启动 `BackgroundTask` 执行耗时查询和 Excel 生成。
4. 生成的文件保存至临时目录或云存储。
5. 任务完成后，通过 WebSocket 通知前端。
6. 前端根据 `task_id` 调用下载接口。

## 14. 后端架构扩展性设计
- **插件化架构**：AI 识别模块支持通过配置切换不同的模型引擎（如本地模型、云端 API）。
- **事件驱动**：引入简单的内部事件总线，当订单状态变更时，自动触发库存更新、通知发送、报表统计等后续操作。
- **多租户预留**：数据库设计中预留了 `tenant_id` 字段，支持未来平滑升级为 SaaS 模式。

## 15. 后端日志与监控规范
- **日志分级**：
  - `DEBUG`: 开发调试信息。
  - `INFO`: 关键业务流程记录（如登录、下单）。
  - `WARNING`: 非致命异常（如缓存失效、参数校验失败）。
  - `ERROR`: 系统错误、数据库连接失败。
- **监控指标 (Prometheus)**：
  - `http_requests_total`: 请求总数。
  - `http_request_duration_seconds`: 请求耗时分布。
  - `db_connection_pool_size`: 数据库连接池占用。

## 16. 后端开发环境搭建指南
1. 安装 Python 3.10+。
2. 创建虚拟环境：`python -m venv venv`。
3. 安装依赖：`pip install -r requirements.txt`。
4. 配置环境变量：复制 `.env.example` 为 `.env` 并修改数据库连接。
5. 初始化数据库：`alembic upgrade head`。
6. 启动服务：`uvicorn main:app --reload`。

## 17. 核心算法与逻辑深度解析 (Algorithms)

### 5.1 零件兼容性匹配算法
- **输入**：用户车型信息（品牌、车系、年款、排量）。
- **逻辑**：
  1. 在 `parts` 表的 `compatible_models` JSON 字段中进行模糊匹配。
  2. 结合 `categories` 表的层级关系，过滤出适配该车型的所有零件。
  3. 根据零件的 `brand` 和 `price` 进行二次排序。
- **示例代码逻辑**：
  ```python
  def match_compatible_parts(car_info):
      query = db.query(Part).filter(
          Part.compatible_models.contains(car_info['brand']),
          Part.compatible_models.contains(car_info['series'])
      )
      return query.all()
  ```

### 5.2 库存周转率计算逻辑
- **公式**：`周转率 = (期间出库总量 / 期间平均库存) * 100%`。
- **实现**：
  1. 从 `inventory_logs` 表中统计指定时间段内的 `type='out'` 的数量总和。
  2. 计算期初库存与期末库存的平均值。
  3. 生成各零件的周转率排名报表。

### 5.3 智能采购建议算法
- **逻辑**：
  1. 监控零件的日均销量（Moving Average）。
  2. 结合当前库存和采购提前期（Lead Time）。
  3. 当 `当前库存 < (日均销量 * 提前期 + 安全库存)` 时，自动生成采购建议。

## 18. 后端安全性实现细节
- **密码哈希**：使用 `passlib` 库的 `bcrypt` 算法，设置 `rounds=12`。
- **JWT 签名**：使用环境变量存储 `SECRET_KEY`，严禁硬编码。
- **输入过滤**：使用 `Pydantic` 的 `Field` 约束（如 `min_length`, `max_length`, `regex`）。
- **SQL 注入防护**：全量使用 SQLAlchemy ORM，禁止使用 `text()` 拼接用户输入。

## 19. 后端性能调优实践
- **数据库连接池**：配置 `pool_pre_ping=True` 防止连接失效。
- **缓存预热**：系统启动时，自动将高频访问的分类数据加载至 Redis。
- **响应压缩**：使用 `GZipMiddleware` 压缩大于 500 字节的响应体。
- **异步任务**：使用 `anyio` 或 `asyncio` 处理非阻塞任务。

## 20. 后端开发规范补充
- **文件命名**：模块名使用小写加下划线，如 `part_service.py`。
- **类命名**：使用大驼峰，如 `PartService`。
- **函数命名**：使用小写加下划线，如 `get_part_by_id`。
- **注释规范**：每个公共函数必须包含 Google 风格的 Docstring。

## 5. 核心模块设计

### 5.1 核心基础模块 (Core Module)
- **功能**：提供系统级的基础设施，包括配置管理、日志记录、异常处理、数据库连接池。
- **设计要点**：
  - 使用 Pydantic 设置全局配置类 `Settings`。
  - 封装统一的日志装饰器，记录每个 API 的入参、出参及执行时间。
  - 实现自定义 `AppException`，支持业务错误码。

### 5.2 认证与授权模块 (Auth Module)
- **功能**：用户注册、登录、Token 签发与校验、RBAC 权限控制。
- **设计要点**：
  - **JWT 机制**：使用 `python-jose` 生成 Access Token，有效期 24 小时。
  - **密码安全**：使用 `passlib` 的 `argon2` 算法进行哈希。
  - **权限依赖**：利用 FastAPI 的 `Depends` 机制实现细粒度的权限校验，例如 `@requires_permission("part:delete")`。

### 5.3 零件与分类模块 (Part Module)
- **功能**：零件的 CRUD、多级分类树构建、兼容性查询。
- **设计要点**：
  - **递归分类**：使用递归算法构建分类树，支持无限级分类。
  - **搜索优化**：集成 SQLAlchemy 的 `match` 函数实现全文检索。
  - **图片处理**：集成 `Pillow` 库，在上传零件图片时自动压缩并生成 WebP 格式以节省带宽。

### 5.4 库存管理模块 (Inventory Module)
- **功能**：入库、出库、库存锁定、预警计算。
- **设计要点**：
  - **事务控制**：在出库操作中，使用数据库事务确保“扣减库存”与“生成出库单”的原子性。
  - **并发处理**：使用 `SELECT ... FOR UPDATE` 悲观锁防止超卖现象。
  - **预警逻辑**：后台定时任务（Celery）每小时扫描一次库存，发现低于 `min_stock` 的零件即向管理员推送通知。

### 5.5 交易与订单模块 (Trade Module)
- **功能**：采购车管理、订单状态机流转。
- **设计要点**：
  - **状态机设计**：定义严格的订单状态流转规则（如：只有 `paid` 状态才能变为 `shipped`）。
  - **订单号生成**：采用“时间戳 + 机器 ID + 随机序列”算法，确保分布式环境下的唯一性。

### 5.6 AI 智能服务模块 (AI Module)
- **功能**：自然语言处理、零件推荐、智能问答。
- **设计要点**：
  - **流式响应**：支持 Server-Sent Events (SSE)，实现 AI 回复的逐字显示。
  - **上下文管理**：在 Redis 中存储用户的对话上下文，实现多轮对话。
  - **Prompt 工程**：针对汽配业务优化 Prompt，确保 AI 能够准确识别 OEM 码和车型信息。

### 5.7 核心业务逻辑实现细节

#### 5.7.1 零件适配性搜索算法
汽配系统的核心难点在于“一车多件”和“一件多车”。
- **实现方式**：
    -   建立 `part_compatibility` 关联表，存储零件 ID 与车型 ID 的映射。
    -   支持模糊搜索：通过零件号（OE 号）、品牌、规格参数进行多维度检索。
    -   使用 SQLAlchemy 的 `joinedload` 优化关联查询，避免 N+1 问题。

#### 5.7.2 库存周转率计算逻辑
系统自动计算零件的周转率，辅助采购决策。
- **公式**：$周转率 = \frac{统计周期内销售总量}{\frac{期初库存 + 期末库存}{2}}$
- **实现**：后台定时任务（Celery Beat）每月初运行，读取历史订单数据，计算结果存入 `part_statistics` 表。

### 5.8 异步任务处理 (Celery & Redis)

系统使用 Celery 处理耗时操作，确保 API 的高响应性：

| 任务名称 | 触发条件 | 处理逻辑 |
| :--- | :--- | :--- |
| `generate_report_pdf` | 用户请求导出报表 | 调用 ReportLab 生成 PDF，完成后通过 WebSocket 通知用户下载 |
| `sync_supplier_price` | 每天凌晨 2 点 | 爬取或调用供应商 API 更新零件参考进货价 |
| `cleanup_expired_tokens` | 每小时 | 清理 Redis 中已过期的 JWT 黑名单 |
| `inventory_alert_check` | 库存变动时 | 检查当前库存是否低于安全水位，发送钉钉/邮件告警 |

### 5.9 缓存设计方案

为了提升查询性能，系统实施了精细化的缓存策略：

1.  **零件详情缓存**：
    -   **Key**: `part:detail:{part_id}`
    -   **策略**: 缓存 24 小时，零件信息修改时主动失效。
2.  **车型分类树缓存**：
    -   **Key**: `category:tree`
    -   **策略**: 永久缓存，仅在后台管理更新分类时刷新。
3.  **用户权限缓存**：
    -   **Key**: `user:perms:{user_id}`
    -   **策略**: 缓存至 Token 过期，减少频繁查询 RBAC 表。

### 5.10 核心 API 实现逻辑深度解析

#### 5.10.1 订单创建事务处理
订单创建涉及多个表的同步更新，必须保证原子性：
```python
@router.post("/orders")
async def create_order(order_data: OrderCreate, db: Session = Depends(get_db)):
    try:
        # 1. 开启事务
        with db.begin():
            # 2. 检查库存并锁定记录 (SELECT FOR UPDATE)
            for item in order_data.items:
                part = db.query(Part).filter(Part.id == item.part_id).with_for_update().one()
                if part.current_stock < item.quantity:
                    raise AppException("库存不足")
                
                # 3. 扣减库存
                part.current_stock -= item.quantity
                
                # 4. 记录库存流水
                db.add(InventoryLog(part_id=part.id, change=-item.quantity, type="SALE"))
            
            # 5. 创建订单主表及详情表
            new_order = Order(user_id=current_user.id, total_amount=order_data.total)
            db.add(new_order)
            db.flush() # 获取订单 ID
            
            for item in order_data.items:
                db.add(OrderDetail(order_id=new_order.id, part_id=item.part_id, price=item.price))
        
        # 6. 事务提交后，触发异步任务（如发送通知）
        background_tasks.add_task(send_order_confirmation, new_order.id)
        return {"status": "success", "order_id": new_order.id}
    except Exception as e:
        db.rollback()
        raise e
```

#### 5.10.2 AI 智能定价模型集成
系统通过调用外部大模型 API，结合历史销售数据提供定价建议：
- **输入特征**：零件 OE 号、品牌、当前库存、过去 30 天平均售价、供应商最新报价。
- **处理流程**：
    1.  后端收集上述特征数据。
    2.  构造 Prompt 发送至 AI 服务模块。
    3.  AI 返回建议价格区间及理由。
    4.  后端缓存结果 1 小时，避免重复调用。

### 5.11 系统日志与监控

系统采用结构化日志记录，便于 ELK 或 Grafana Loki 收集：
- **访问日志**：记录所有 API 请求的 Method, Path, Status Code, Latency。
- **业务日志**：记录关键业务状态变更，包含 `trace_id` 以便全链路追踪。
- **错误日志**：记录异常堆栈信息，并自动触发告警。

### 5.12 数据库迁移管理 (Alembic)

系统使用 Alembic 进行版本控制，严禁手动修改生产环境数据库结构：

1.  **创建迁移**：`alembic revision --autogenerate -m "add_new_table"`
2.  **检查脚本**：人工审核 `versions/` 下生成的 Python 脚本。
3.  **执行迁移**：`alembic upgrade head`
4.  **回滚操作**：`alembic downgrade -1`
