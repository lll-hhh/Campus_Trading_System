# 05_MODULE_DESIGN_BACKEND.md

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