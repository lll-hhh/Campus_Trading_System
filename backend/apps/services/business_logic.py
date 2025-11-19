"""
完整功能实现模块 - 商品、订单、收藏、评论等
这个文件包含所有空壳功能的数据库操作实现
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import select, and_, func, or_, desc
from sqlalchemy.orm import Session
from apps.core.models import (
    Item, Category, User, ItemMedia, Favorite, Comment,
    Transaction, Review, Follow
)


class ItemService:
    """商品服务"""
    
    @staticmethod
    def create_item(
        session: Session,
        seller_id: int,
        title: str,
        description: str,
        price: float,
        category_name: str,
        images: List[str],
        status: str = "draft",
        condition: str = "good"
    ) -> Item:
        """创建商品"""
        # 获取或创建分类
        category = session.execute(
            select(Category).where(Category.name == category_name)
        ).scalar_one_or_none()
        
        if not category:
            category = Category(name=category_name, description=f"{category_name}分类")
            session.add(category)
            session.flush()
        
        # 创建商品
        item = Item(
            seller_id=seller_id,
            category_id=category.id,
            title=title,
            description=description,
            price=price,
            currency="CNY",
            status=status,
            condition=condition,
            view_count=0
        )
        session.add(item)
        session.flush()
        
        # 添加图片
        for img_url in images:
            media = ItemMedia(item_id=item.id, media_type="image", url=img_url)
            session.add(media)
        
        session.commit()
        session.refresh(item)
        return item
    
    @staticmethod
    def get_items(
        session: Session,
        page: int = 1,
        page_size: int = 20,
        category: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        keyword: Optional[str] = None,
        status: str = "available"
    ) -> tuple[List[Item], int]:
        """获取商品列表"""
        # 构建查询
        query = select(Item)
        conditions = [Item.status == status] if status else []
        
        # 分类过滤
        if category:
            cat = session.execute(
                select(Category).where(Category.name == category)
            ).scalar_one_or_none()
            if cat:
                conditions.append(Item.category_id == cat.id)
        
        # 价格过滤
        if min_price is not None:
            conditions.append(Item.price >= min_price)
        if max_price is not None:
            conditions.append(Item.price <= max_price)
        
        # 关键词搜索
        if keyword:
            conditions.append(
                or_(
                    Item.title.contains(keyword),
                    Item.description.contains(keyword)
                )
            )
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # 总数
        count_query = select(func.count()).select_from(Item).where(and_(*conditions))
        total = session.execute(count_query).scalar() or 0
        
        # 分页和排序
        query = query.order_by(desc(Item.created_at))
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        items = session.execute(query).scalars().all()
        return list(items), total
    
    @staticmethod
    def get_item_detail(session: Session, item_id: int) -> Optional[Item]:
        """获取商品详情"""
        item = session.get(Item, item_id)
        if item:
            # 增加浏览量
            item.view_count += 1
            session.commit()
        return item
    
    @staticmethod
    def update_item(
        session: Session,
        item_id: int,
        seller_id: int,
        **kwargs
    ) -> Optional[Item]:
        """更新商品"""
        item = session.get(Item, item_id)
        if not item or item.seller_id != seller_id:
            return None
        
        # 更新字段
        for key, value in kwargs.items():
            if hasattr(item, key) and value is not None:
                setattr(item, key, value)
        
        session.commit()
        session.refresh(item)
        return item
    
    @staticmethod
    def delete_item(session: Session, item_id: int, seller_id: int) -> bool:
        """删除商品"""
        item = session.get(Item, item_id)
        if not item or item.seller_id != seller_id:
            return False
        
        session.delete(item)
        session.commit()
        return True


class FavoriteService:
    """收藏服务"""
    
    @staticmethod
    def toggle_favorite(session: Session, user_id: int, item_id: int) -> Dict[str, Any]:
        """切换收藏状态"""
        # 检查商品是否存在
        item = session.get(Item, item_id)
        if not item:
            return {"success": False, "message": "商品不存在"}
        
        # 查找收藏记录
        favorite = session.execute(
            select(Favorite).where(
                and_(Favorite.user_id == user_id, Favorite.item_id == item_id)
            )
        ).scalar_one_or_none()
        
        if favorite:
            # 取消收藏
            session.delete(favorite)
            session.commit()
            return {"success": True, "action": "removed", "favorited": False}
        else:
            # 添加收藏
            new_favorite = Favorite(user_id=user_id, item_id=item_id)
            session.add(new_favorite)
            session.commit()
            return {"success": True, "action": "added", "favorited": True}
    
    @staticmethod
    def get_user_favorites(
        session: Session,
        user_id: int,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[Item], int]:
        """获取用户收藏列表"""
        # 查询收藏的商品ID
        query = select(Favorite).where(Favorite.user_id == user_id)
        
        # 总数
        total = session.execute(
            select(func.count()).select_from(Favorite).where(Favorite.user_id == user_id)
        ).scalar() or 0
        
        # 分页
        query = query.order_by(desc(Favorite.created_at))
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        favorites = session.execute(query).scalars().all()
        item_ids = [f.item_id for f in favorites]
        
        # 获取商品详情
        if item_ids:
            items = session.execute(
                select(Item).where(Item.id.in_(item_ids))
            ).scalars().all()
            return list(items), total
        
        return [], total
    
    @staticmethod
    def is_favorited(session: Session, user_id: int, item_id: int) -> bool:
        """检查是否已收藏"""
        favorite = session.execute(
            select(Favorite).where(
                and_(Favorite.user_id == user_id, Favorite.item_id == item_id)
            )
        ).scalar_one_or_none()
        return favorite is not None


class CommentService:
    """评论服务"""
    
    @staticmethod
    def create_comment(
        session: Session,
        item_id: int,
        user_id: int,
        content: str,
        rating: int = 5,
        parent_comment_id: Optional[int] = None
    ) -> Comment:
        """创建评论"""
        comment = Comment(
            item_id=item_id,
            user_id=user_id,
            content=content,
            rating=rating,
            parent_comment_id=parent_comment_id
        )
        session.add(comment)
        session.commit()
        session.refresh(comment)
        return comment
    
    @staticmethod
    def get_item_comments(
        session: Session,
        item_id: int,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[Comment], int]:
        """获取商品评论"""
        # 只获取顶级评论
        query = select(Comment).where(
            and_(Comment.item_id == item_id, Comment.parent_comment_id.is_(None))
        )
        
        # 总数
        total = session.execute(
            select(func.count()).select_from(Comment).where(
                and_(Comment.item_id == item_id, Comment.parent_comment_id.is_(None))
            )
        ).scalar() or 0
        
        # 分页
        query = query.order_by(desc(Comment.created_at))
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        comments = session.execute(query).scalars().all()
        return list(comments), total
    
    @staticmethod
    def delete_comment(session: Session, comment_id: int, user_id: int) -> bool:
        """删除评论"""
        comment = session.get(Comment, comment_id)
        if not comment or comment.user_id != user_id:
            return False
        
        session.delete(comment)
        session.commit()
        return True


class TransactionService:
    """交易服务"""
    
    @staticmethod
    def create_transaction(
        session: Session,
        buyer_id: int,
        item_id: int,
        quantity: int = 1,
        note: Optional[str] = None
    ) -> Optional[Transaction]:
        """创建交易订单"""
        # 检查商品
        item = session.get(Item, item_id)
        if not item or item.status != "available":
            return None
        
        # 创建交易
        transaction = Transaction(
            buyer_id=buyer_id,
            seller_id=item.seller_id,
            item_id=item_id,
            quantity=quantity,
            price=item.price,
            total_amount=item.price * quantity,
            status="pending",
            note=note
        )
        session.add(transaction)
        
        # 更新商品状态
        item.status = "sold"
        
        session.commit()
        session.refresh(transaction)
        return transaction
    
    @staticmethod
    def get_user_transactions(
        session: Session,
        user_id: int,
        role: str = "buyer",  # buyer or seller
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[Transaction], int]:
        """获取用户交易列表"""
        if role == "buyer":
            condition = Transaction.buyer_id == user_id
        else:
            condition = Transaction.seller_id == user_id
        
        query = select(Transaction).where(condition)
        
        # 总数
        total = session.execute(
            select(func.count()).select_from(Transaction).where(condition)
        ).scalar() or 0
        
        # 分页
        query = query.order_by(desc(Transaction.created_at))
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        transactions = session.execute(query).scalars().all()
        return list(transactions), total
    
    @staticmethod
    def update_transaction_status(
        session: Session,
        transaction_id: int,
        user_id: int,
        new_status: str
    ) -> Optional[Transaction]:
        """更新交易状态"""
        transaction = session.get(Transaction, transaction_id)
        if not transaction:
            return None
        
        # 验证权限
        if transaction.buyer_id != user_id and transaction.seller_id != user_id:
            return None
        
        transaction.status = new_status
        session.commit()
        session.refresh(transaction)
        return transaction


# 导出所有服务
__all__ = [
    "ItemService",
    "FavoriteService", 
    "CommentService",
    "TransactionService"
]
