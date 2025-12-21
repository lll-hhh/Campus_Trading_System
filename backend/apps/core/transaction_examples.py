"""
Transaction management usage examples.

This module demonstrates best practices for using transactions
in CampuSwap multi-database environment.
"""
from datetime import datetime
from typing import List

from sqlalchemy.orm import Session
from sqlalchemy import func

from apps.core.database import db_manager
from apps.core.models import User, Item, Transaction
from apps.core.transaction import (
    with_transaction,
    transactional_scope,
    read_only_transaction,
    IsolationLevel,
)


# ========================================
# Example 1: 简单事务(自动提交/回滚)
# ========================================

@with_transaction("mysql")
def create_new_item(
    session: Session,
    seller_id: int,
    title: str,
    price: float,
    category: str,
) -> int:
    """
    创建新商品(单表插入)
    
    隔离级别: REPEATABLE READ (MySQL 默认)
    自动处理: commit on success, rollback on error
    """
    item = Item(
        seller_id=seller_id,
        title=title,
        price=price,
        category=category,
        status='active',
        created_at=datetime.utcnow(),
    )
    session.add(item)
    session.flush()  # 获取自增 ID
    return item.id


# ========================================
# Example 2: 跨表事务(ACID 保证)
# ========================================

@with_transaction("mysql", max_retries=5)
def create_transaction_with_inventory_update(
    session: Session,
    buyer_id: int,
    seller_id: int,
    item_id: int,
    price: float,
) -> int:
    """
    创建交易并更新商品状态(原子操作)
    
    业务逻辑:
    1. 锁定商品(防止重复售卖)
    2. 验证商品状态
    3. 创建交易记录
    4. 更新商品状态为已售
    
    并发控制: 悲观锁 (FOR UPDATE)
    死锁处理: 自动重试最多 5 次
    """
    # Step 1: 锁定商品行(阻塞其他购买请求)
    item = session.query(Item).filter_by(id=item_id).with_for_update().one()
    
    # Step 2: 验证商品可售
    if item.status != 'active':
        raise ValueError(f"Item {item_id} is not available (status: {item.status})")
    
    if item.seller_id == buyer_id:
        raise ValueError("Cannot buy your own item")
    
    # Step 3: 创建交易记录
    transaction = Transaction(
        buyer_id=buyer_id,
        seller_id=seller_id,
        item_id=item_id,
        amount=price,
        status='pending',
        created_at=datetime.utcnow(),
    )
    session.add(transaction)
    
    # Step 4: 更新商品状态
    item.status = 'sold'
    item.sold_at = datetime.utcnow()
    
    # Flush 触发数据库触发器(audit_logs, sync_version)
    session.flush()
    
    return transaction.id


# ========================================
# Example 3: 嵌套事务(SAVEPOINT)
# ========================================

def process_bulk_orders(session: Session, orders: List[dict]) -> List[dict]:
    """
    批量处理订单,失败订单不影响成功订单
    
    实现方式: SAVEPOINT(部分回滚)
    场景: 批量导入,允许部分失败
    """
    results = []
    
    for order in orders:
        try:
            # 使用 SAVEPOINT 创建嵌套事务
            with transactional_scope(session, savepoint=True):
                item = session.query(Item).filter_by(id=order['item_id']).one()
                
                # 验证并更新
                if item.status != 'active':
                    raise ValueError(f"Item {item.id} unavailable")
                
                item.status = 'reserved'
                item.reserved_by = order['buyer_id']
                
                results.append({
                    'order_id': order['id'],
                    'status': 'success',
                    'item_id': item.id,
                })
        except Exception as e:
            # SAVEPOINT 回滚,不影响其他订单
            results.append({
                'order_id': order['id'],
                'status': 'failed',
                'error': str(e),
            })
    
    # 外层事务提交所有成功的订单
    return results


# ========================================
# Example 4: 只读事务(性能优化)
# ========================================

def get_market_statistics(session: Session) -> dict:
    """
    获取市场统计数据(无锁读取)
    
    优化点:
    - 声明 READ ONLY 事务
    - 利用 MVCC 快照读
    - 减少锁竞争
    """
    with read_only_transaction(session):
        stats = {
            'total_items': session.query(Item).count(),
            'active_items': session.query(Item).filter_by(status='active').count(),
            'sold_items': session.query(Item).filter_by(status='sold').count(),
            'avg_price': session.query(func.avg(Item.price)).scalar() or 0.0,
            'total_users': session.query(User).count(),
            'total_transactions': session.query(Transaction).count(),
        }
        return stats


# ========================================
# Example 5: 临时提升隔离级别
# ========================================

def calculate_user_reputation(session: Session, user_id: int) -> float:
    """
    计算用户信誉分(需要快照一致性)
    
    场景: 多次查询需要看到一致的数据版本
    方案: 临时提升到 SERIALIZABLE
    """
    with transactional_scope(session, isolation_level=IsolationLevel.SERIALIZABLE):
        # 同一快照内的多次查询
        user = session.query(User).filter_by(id=user_id).one()
        
        # 统计交易次数
        buy_count = session.query(Transaction).filter_by(buyer_id=user_id).count()
        sell_count = session.query(Transaction).filter_by(seller_id=user_id).count()
        
        # 计算平均评分(假设有 ratings 表)
        avg_rating = 4.5  # 简化示例
        
        # 计算信誉分
        reputation = (buy_count * 0.3 + sell_count * 0.5 + avg_rating * 20) / 100
        
        # 更新用户信誉
        user.reputation_score = reputation
        session.flush()
        
        return reputation


# ========================================
# Example 6: 防止死锁(锁定顺序)
# ========================================

@with_transaction("mysql", max_retries=3)
def transfer_item_ownership(
    session: Session,
    from_user_id: int,
    to_user_id: int,
    item_id: int,
) -> None:
    """
    转移商品所有权(防止死锁)
    
    关键: 按主键升序加锁
    避免: 事务 A 锁 user1→user2, 事务 B 锁 user2→user1
    """
    # 按 ID 升序锁定(关键!)
    user_ids = sorted([from_user_id, to_user_id])
    users = session.query(User).filter(
        User.id.in_(user_ids)
    ).order_by(User.id).with_for_update().all()
    
    # 验证用户存在
    if len(users) != 2:
        raise ValueError("One or both users not found")
    
    # 锁定商品
    item = session.query(Item).filter_by(id=item_id).with_for_update().one()
    
    # 验证所有权
    if item.seller_id != from_user_id:
        raise ValueError(f"User {from_user_id} does not own item {item_id}")
    
    # 转移所有权
    item.seller_id = to_user_id
    item.transferred_at = datetime.utcnow()
    
    session.flush()


# ========================================
# Example 7: 批量操作优化
# ========================================

@with_transaction("mysql")
def bulk_create_items(session: Session, items_data: List[dict]) -> List[int]:
    """
    批量创建商品(优化性能)
    
    优化:
    - bulk_insert_mappings 减少往返
    - 批量刷新避免 N+1 查询
    """
    # 使用 bulk_insert_mappings(比逐个 add 快 10x)
    session.bulk_insert_mappings(Item, items_data)
    session.flush()
    
    # 获取插入的 ID(需要重新查询)
    # 注意: bulk_insert_mappings 不返回生成的 ID
    titles = [item['title'] for item in items_data]
    created_items = session.query(Item).filter(Item.title.in_(titles)).all()
    
    return [item.id for item in created_items]


# ========================================
# Example 8: 长事务拆分
# ========================================

def process_large_dataset_in_batches(item_ids: List[int], batch_size: int = 100):
    """
    分批处理大数据集(避免长事务)
    
    问题: 一次处理 10000 条记录会锁定太久
    方案: 拆分为 100 条/批,独立事务
    """
    for i in range(0, len(item_ids), batch_size):
        batch = item_ids[i:i + batch_size]
        
        # 每批独立事务
        with db_manager.session_scope("mysql") as session:
            items = session.query(Item).filter(Item.id.in_(batch)).all()
            
            for item in items:
                # 业务处理
                item.processed = True
                item.processed_at = datetime.utcnow()
            
            session.flush()
        # 提交后释放锁,其他事务可以继续


# ========================================
# Example 9: 跨数据库事务(分布式场景)
# ========================================

def sync_item_to_all_databases(item_data: dict) -> dict:
    """
    将商品同步到所有数据库
    
    注意: 不是真正的分布式事务(无 2PC)
    策略: 最终一致性(通过 Redis Streams)
    """
    results = {}
    
    for db_name in ["mysql", "mariadb", "postgres", "sqlite"]:
        try:
            with db_manager.session_scope(db_name) as session:
                item = Item(**item_data)
                session.add(item)
                session.flush()
                
                results[db_name] = {
                    'status': 'success',
                    'item_id': item.id,
                }
        except Exception as e:
            results[db_name] = {
                'status': 'failed',
                'error': str(e),
            }
    
    return results


# ========================================
# Example 10: 监控事务指标
# ========================================

def monitor_transaction_health():
    """
    监控事务健康状况
    
    指标:
    - 重试率
    - 死锁频率
    - 平均执行时间
    """
    from apps.core.transaction import transaction_metrics
    
    stats = transaction_metrics.get_stats()
    
    # 告警阈值
    if stats['retry_rate'] > 0.1:  # 重试率超过 10%
        print(f"⚠️ HIGH RETRY RATE: {stats['retry_rate']:.1%}")
    
    if stats['total_deadlocks'] > 100:
        print(f"⚠️ MANY DEADLOCKS: {stats['total_deadlocks']}")
    
    if stats['avg_duration_seconds'] > 1.0:
        print(f"⚠️ SLOW TRANSACTIONS: {stats['avg_duration_seconds']:.3f}s")
    
    return stats


# ========================================
# 使用示例
# ========================================

if __name__ == "__main__":
    # Example 1: 创建商品
    with db_manager.session_scope("mysql") as session:
        item_id = create_new_item(
            session=session,
            seller_id=1,
            title="iPhone 13 Pro",
            price=4999.0,
            category="electronics",
        )
        print(f"✅ Created item: {item_id}")
    
    # Example 2: 创建交易
    with db_manager.session_scope("mysql") as session:
        try:
            tx_id = create_transaction_with_inventory_update(
                session=session,
                buyer_id=2,
                seller_id=1,
                item_id=item_id,
                price=4999.0,
            )
            print(f"✅ Created transaction: {tx_id}")
        except ValueError as e:
            print(f"❌ Transaction failed: {e}")
    
    # Example 4: 市场统计
    with db_manager.session_scope("mysql") as session:
        stats = get_market_statistics(session)
        print(f"📊 Market stats: {stats}")
    
    # Example 10: 监控
    health = monitor_transaction_health()
    print(f"💊 Transaction health: {health}")
