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
    Transaction
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
        # 首先尝试将slug转换为category_name
        slug_to_name_map = {
            "electronics": "数码产品",
            "books": "图书教材", 
            "daily": "生活用品",
            "sports": "运动器材",
            "fashion": "服装鞋包",
            "beauty": "美妆护肤",
            "other": "其他闲置",
            # PublishItemView使用的slug
            "digital": "数码产品",
            "clothing": "服装鞋包",
            "entertainment": "其他闲置",
            "stationery": "其他闲置",
            "music": "其他闲置",
            "bicycle": "运动器材"
        }
        
        # 如果输入的是slug，转换为name
        actual_category_name = slug_to_name_map.get(category_name, category_name)
        
        # 获取或创建分类
        category = session.execute(
            select(Category).where(Category.name == actual_category_name)
        ).scalar_one_or_none()
        
        if not category:
            category_slug = {
                "数码产品": "electronics",
                "图书教材": "books",
                "生活用品": "daily", 
                "运动器材": "sports",
                "服装鞋包": "fashion",
                "美妆护肤": "beauty",
                "其他闲置": "other"
            }.get(actual_category_name, actual_category_name.lower())
            
            category = Category(name=actual_category_name, slug=category_slug, description=f"{actual_category_name}分类")
            session.add(category)
            session.flush()
        
        # ✅ 映射 condition 到 condition_type
        condition_map = {
            "new": "全新",
            "like_new": "99新",
            "very_good": "95新",
            "good": "9成新",
            "used": "二手",
        }
        condition_type = condition_map.get(condition, "二手")
        
        # 创建商品（不包含 currency 和 condition 字段）
        item = Item(
            seller_id=seller_id,
            category_id=category.id,
            title=title,
            description=description,
            price=price,
            condition_type=condition_type,  # ✅ 使用正确的字段名
            status=status,
            view_count=0
        )
        session.add(item)
        session.flush()
        
        # 添加图片
        for idx, img_url in enumerate(images):
            media = ItemMedia(
                item_id=item.id,
                image_url=img_url,
                sort_order=idx,
                is_cover=(idx == 0)
            )
            session.add(media)
        
        session.flush()
        return item
    
    @staticmethod
    def get_items(
        session: Session,
        page: int = 1,
        page_size: int = 20,
        category: Optional[str] = None,
        condition: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        keyword: Optional[str] = None,
        status: Optional[str] = "available",
        seller_id: Optional[int] = None
    ) -> tuple[List[Item], int]:
        """获取商品列表"""
        # 构建查询
        query = select(Item)
        conditions = []
        if status and status != "all":
            conditions.append(Item.status == status)
        if seller_id:
            conditions.append(Item.seller_id == seller_id)
        
        # 分类过滤
        if category:
            cat = session.execute(
                select(Category).where(Category.slug == category)
            ).scalar_one_or_none()
            if cat:
                conditions.append(Item.category_id == cat.id)
        
        # 成色过滤 - 直接使用中文值匹配数据库字段
        if condition:
            # 支持英文和中文两种格式
            condition_map = {
                'new': '全新',
                'like_new': '99新',
                'very_good': '95新',
                'good': '9成新',
                'used': '二手'
            }
            # 如果是英文则转换，否则直接使用
            db_condition = condition_map.get(condition, condition)
            conditions.append(Item.condition_type == db_condition)
        
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
        count_query = select(func.count()).select_from(Item)
        if conditions:
            count_query = count_query.where(and_(*conditions))
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
                # 特殊处理 condition 字段，映射到 condition_type
                if key == 'condition':
                    condition_mapping = {
                        'new': '全新',
                        'good': '9成新', 
                        'fair': '二手',
                        'poor': '二手'
                    }
                    item.condition_type = condition_mapping.get(value, '二手')
                else:
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
        parent_id: Optional[int] = None
    ) -> Comment:
        """创建评论"""
        comment = Comment(
            item_id=item_id,
            user_id=user_id,
            content=content,
            rating=rating,
            parent_id=parent_id
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
            and_(Comment.item_id == item_id, Comment.parent_id.is_(None))
        )
        
        # 总数
        total = session.execute(
            select(func.count()).select_from(Comment).where(
                and_(Comment.item_id == item_id, Comment.parent_id.is_(None))
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
        buyer_contact: Optional[str] = None
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
            item_price=float(item.price),
            final_amount=float(item.price),
            status="pending",
            buyer_contact=buyer_contact
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


class MessageService:
    """消息服务"""
    
    @staticmethod
    def get_or_create_conversation(
        session: Session,
        user1_id: int,
        user2_id: int,
        item_id: Optional[int] = None
    ):
        """获取或创建会话"""
        from apps.core.models import Conversation
        
        # 查找已有会话（双向）
        conv = session.execute(
            select(Conversation).where(
                or_(
                    and_(Conversation.user1_id == user1_id, Conversation.user2_id == user2_id),
                    and_(Conversation.user1_id == user2_id, Conversation.user2_id == user1_id)
                )
            )
        ).scalar_one_or_none()
        
        if not conv:
            conv = Conversation(
                user1_id=user1_id,
                user2_id=user2_id,
                item_id=item_id,
                user1_unread_count=0,
                user2_unread_count=0
            )
            session.add(conv)
            session.flush()
        
        return conv
    
    @staticmethod
    def send_message(
        session: Session,
        sender_id: int,
        receiver_id: int,
        content: str,
        item_id: Optional[int] = None
    ):
        """发送消息"""
        from apps.core.models import Message
        
        # 验证接收者存在
        receiver = session.get(User, receiver_id)
        if not receiver:
            raise ValueError("接收者不存在")
        
        # 不能给自己发消息
        if sender_id == receiver_id:
            raise ValueError("不能给自己发送消息")
        
        # 获取或创建会话
        conv = MessageService.get_or_create_conversation(session, sender_id, receiver_id, item_id)
        
        # 创建消息
        message = Message(
            sender_id=sender_id,
            receiver_id=receiver_id,
            content=content,
            item_id=item_id,
            is_read=False
        )
        session.add(message)
        session.flush()  # 获取 message.id
        
        # 更新会话的未读计数和最后消息
        conv.last_message_content = content[:100] if len(content) > 100 else content
        conv.last_message_at = datetime.utcnow()
        conv.last_message_id = message.id
        
        # 增加对方的未读计数
        if conv.user1_id == sender_id:
            conv.user2_unread_count = (conv.user2_unread_count or 0) + 1
        else:
            conv.user1_unread_count = (conv.user1_unread_count or 0) + 1
        
        session.flush()
        session.refresh(message)
        
        # 获取发送者信息
        sender = session.get(User, sender_id)
        
        return {
            "id": message.id,
            "conversation_id": conv.id,
            "sender_id": sender_id,
            "sender_name": sender.username if sender else "未知用户",
            "sender_avatar": sender.avatar_url if sender else None,
            "receiver_id": receiver_id,
            "receiver_name": receiver.username,
            "receiver_avatar": receiver.avatar_url if receiver else None,
            "content": message.content,
            "message_type": "text",
            "item_id": message.item_id,
            "is_read": message.is_read,
            "created_at": message.created_at
        }
    
    @staticmethod
    def get_conversations(session: Session, user_id: int):
        """获取用户的会话列表"""
        from apps.core.models import Conversation
        
        # 查询用户参与的所有会话
        convs = session.execute(
            select(Conversation).where(
                or_(
                    Conversation.user1_id == user_id,
                    Conversation.user2_id == user_id
                )
            ).order_by(desc(Conversation.last_message_at))
        ).scalars().all()
        
        result = []
        total_unread = 0
        
        for conv in convs:
            conv_data = MessageService.serialize_conversation(session, conv, user_id)
            total_unread += conv_data["unread_count"]
            result.append(conv_data)
        
        return {
            "conversations": result,
            "total": len(result),
            "total_unread": total_unread
        }

    @staticmethod
    def serialize_conversation(session: Session, conv, user_id: int):
        """序列化会话为API响应格式"""
        other_user_id = conv.user2_id if conv.user1_id == user_id else conv.user1_id
        other_user = session.get(User, other_user_id)
        unread_count = conv.user1_unread_count if conv.user1_id == user_id else conv.user2_unread_count
        unread_count = unread_count or 0
        return {
            "id": conv.id,
            "other_user_id": other_user_id,
            "other_user_name": other_user.username if other_user else "未知用户",
            "other_user_avatar": other_user.avatar_url if other_user else None,
            "last_message": conv.last_message_content,
            "last_message_time": conv.last_message_at,
            "unread_count": unread_count,
            "created_at": conv.created_at
        }
    
    @staticmethod
    def get_conversation_messages(
        session: Session,
        user_id: int,
        conversation_id: int,
        page: int = 1,
        page_size: int = 50
    ):
        """获取会话消息列表"""
        from apps.core.models import Conversation, Message
        
        # 验证会话权限
        conv = session.get(Conversation, conversation_id)
        if not conv:
            raise ValueError("会话不存在")
        
        if conv.user1_id != user_id and conv.user2_id != user_id:
            raise ValueError("无权访问此会话")
        
        other_user_id = conv.user2_id if conv.user1_id == user_id else conv.user1_id
        
        # 查询消息
        query = select(Message).where(
            or_(
                and_(Message.sender_id == user_id, Message.receiver_id == other_user_id),
                and_(Message.sender_id == other_user_id, Message.receiver_id == user_id)
            ),
            # 排除用户已删除的消息
            or_(
                and_(Message.sender_id == user_id, not Message.is_deleted_by_sender),
                and_(Message.receiver_id == user_id, not Message.is_deleted_by_receiver)
            )
        ).order_by(desc(Message.created_at))
        
        # 总数
        total_query = select(func.count()).select_from(Message).where(
            or_(
                and_(Message.sender_id == user_id, Message.receiver_id == other_user_id),
                and_(Message.sender_id == other_user_id, Message.receiver_id == user_id)
            )
        )
        total = session.execute(total_query).scalar() or 0
        
        # 分页
        query = query.offset((page - 1) * page_size).limit(page_size)
        messages = session.execute(query).scalars().all()
        
        # 获取用户信息
        current_user = session.get(User, user_id)
        other_user = session.get(User, other_user_id)
        
        result = []
        for msg in messages:
            is_sender = msg.sender_id == user_id
            result.append({
                "id": msg.id,
                "conversation_id": conversation_id,
                "sender_id": msg.sender_id,
                "sender_name": current_user.username if is_sender else (other_user.username if other_user else "未知用户"),
                "sender_avatar": current_user.avatar_url if is_sender else (other_user.avatar_url if other_user else None),
                "receiver_id": msg.receiver_id,
                "receiver_name": other_user.username if is_sender else current_user.username,
                "receiver_avatar": other_user.avatar_url if is_sender else current_user.avatar_url,
                "content": msg.content,
                "message_type": "text",
                "item_id": msg.item_id,
                "is_read": msg.is_read,
                "created_at": msg.created_at
            })
        
        # 标记接收的消息为已读
        MessageService.mark_conversation_read(session, user_id, conversation_id)
        
        return {
            "messages": result,
            "total": total,
            "page": page,
            "page_size": page_size
        }
    
    @staticmethod
    def mark_message_read(session: Session, user_id: int, message_id: int):
        """标记消息为已读"""
        from apps.core.models import Message
        
        message = session.get(Message, message_id)
        if not message:
            raise ValueError("消息不存在")
        
        if message.receiver_id != user_id:
            raise ValueError("无权操作此消息")
        
        message.is_read = True
        message.read_at = datetime.utcnow()
        session.flush()
        
        return {"message": "消息已标记为已读", "message_id": message_id}
    
    @staticmethod
    def mark_conversation_read(session: Session, user_id: int, conversation_id: int):
        """标记会话所有消息为已读"""
        from apps.core.models import Conversation, Message
        
        conv = session.get(Conversation, conversation_id)
        if not conv:
            raise ValueError("会话不存在")
        
        if conv.user1_id != user_id and conv.user2_id != user_id:
            raise ValueError("无权操作此会话")
        
        other_user_id = conv.user2_id if conv.user1_id == user_id else conv.user1_id
        
        # 批量更新未读消息
        now = datetime.utcnow()
        session.execute(
            Message.__table__.update().where(
                and_(
                    Message.sender_id == other_user_id,
                    Message.receiver_id == user_id,
                    not Message.is_read
                )
            ).values(is_read=True, read_at=now)
        )
        
        # 重置未读计数
        if conv.user1_id == user_id:
            conv.unread_count_user1 = 0
        else:
            conv.unread_count_user2 = 0
        
        session.flush()
        
        return {"message": "会话消息已全部标记为已读", "conversation_id": conversation_id}
    
    @staticmethod
    def delete_conversation(session: Session, user_id: int, conversation_id: int):
        """删除会话（软删除，只是隐藏）"""
        from apps.core.models import Conversation, Message
        
        conv = session.get(Conversation, conversation_id)
        if not conv:
            raise ValueError("会话不存在")
        
        if conv.user1_id != user_id and conv.user2_id != user_id:
            raise ValueError("无权操作此会话")
        
        other_user_id = conv.user2_id if conv.user1_id == user_id else conv.user1_id
        
        # 软删除该用户的所有消息
        # 作为发送者
        session.execute(
            Message.__table__.update().where(
                and_(
                    Message.sender_id == user_id,
                    Message.receiver_id == other_user_id
                )
            ).values(is_deleted_by_sender=True)
        )
        
        # 作为接收者
        session.execute(
            Message.__table__.update().where(
                and_(
                    Message.sender_id == other_user_id,
                    Message.receiver_id == user_id
                )
            ).values(is_deleted_by_receiver=True)
        )
        
        session.flush()
        
        return {"message": "会话已删除", "conversation_id": conversation_id}
    
    @staticmethod
    def get_unread_count(session: Session, user_id: int):
        """获取未读消息统计"""
        from apps.core.models import Conversation
        
        # 查询用户参与的所有会话
        convs = session.execute(
            select(Conversation).where(
                or_(
                    Conversation.user1_id == user_id,
                    Conversation.user2_id == user_id
                )
            )
        ).scalars().all()
        
        total_unread = 0
        conversations_with_unread = 0
        
        for conv in convs:
            unread = conv.unread_count_user1 if conv.user1_id == user_id else conv.unread_count_user2
            unread = unread or 0
            total_unread += unread
            if unread > 0:
                conversations_with_unread += 1
        
        return {
            "total_unread": total_unread,
            "conversations_with_unread": conversations_with_unread
        }
    
    @staticmethod
    def search_messages(
        session: Session,
        user_id: int,
        keyword: str,
        page: int = 1,
        page_size: int = 20
    ):
        """搜索消息"""
        from apps.core.models import Message
        
        # 查询包含关键词的消息
        query = select(Message).where(
            and_(
                or_(Message.sender_id == user_id, Message.receiver_id == user_id),
                Message.content.ilike(f"%{keyword}%")
            )
        ).order_by(desc(Message.created_at))
        
        # 总数
        total_query = select(func.count()).select_from(Message).where(
            and_(
                or_(Message.sender_id == user_id, Message.receiver_id == user_id),
                Message.content.ilike(f"%{keyword}%")
            )
        )
        total = session.execute(total_query).scalar() or 0
        
        # 分页
        query = query.offset((page - 1) * page_size).limit(page_size)
        messages = session.execute(query).scalars().all()
        
        result = []
        for msg in messages:
            sender = session.get(User, msg.sender_id)
            receiver = session.get(User, msg.receiver_id)
            result.append({
                "id": msg.id,
                "sender_id": msg.sender_id,
                "sender_name": sender.username if sender else "未知用户",
                "receiver_id": msg.receiver_id,
                "receiver_name": receiver.username if receiver else "未知用户",
                "content": msg.content,
                "created_at": msg.created_at
            })
        
        return {
            "results": result,
            "total": total,
            "keyword": keyword
        }


class SearchService:
    """搜索服务"""
    
    @staticmethod
    def search_items(
        session: Session,
        keyword: str,
        category: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        status: str = "available",
        sort_by: str = "relevance",
        page: int = 1,
        page_size: int = 20,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """高级搜索商品"""
        from apps.core.models import Item, Category, ItemMedia
        
        # 构建基础查询
        query = select(Item).where(Item.status == status)
        conditions = []
        
        # 关键词搜索（标题和描述）
        if keyword:
            keyword_condition = or_(
                Item.title.ilike(f"%{keyword}%"),
                Item.description.ilike(f"%{keyword}%")
            )
            conditions.append(keyword_condition)
        
        # 分类筛选
        if category:
            cat = session.execute(
                select(Category).where(Category.name == category)
            ).scalar_one_or_none()
            if cat:
                conditions.append(Item.category_id == cat.id)
        
        # 价格区间
        if min_price is not None:
            conditions.append(Item.price >= min_price)
        if max_price is not None:
            conditions.append(Item.price <= max_price)
        
        # 应用条件
        if conditions:
            query = query.where(and_(*conditions))
        
        # 计算总数
        count_query = select(func.count()).select_from(Item).where(Item.status == status)
        if conditions:
            count_query = count_query.where(and_(*conditions))
        total = session.execute(count_query).scalar() or 0
        
        # 排序
        if sort_by == "price_asc":
            query = query.order_by(Item.price.asc())
        elif sort_by == "price_desc":
            query = query.order_by(Item.price.desc())
        elif sort_by == "time_desc":
            query = query.order_by(desc(Item.created_at))
        elif sort_by == "popular":
            query = query.order_by(desc(Item.view_count))
        else:  # relevance - 默认按相关度（这里简单用浏览量）
            query = query.order_by(desc(Item.view_count))
        
        # 分页
        query = query.offset((page - 1) * page_size).limit(page_size)
        items = session.execute(query).scalars().all()
        
        # 构建结果
        result_items = []
        for item in items:
            # 获取卖家信息
            seller = session.get(User, item.seller_id)
            # 获取分类信息
            cat = session.get(Category, item.category_id) if item.category_id else None
            # 获取封面图片
            cover_image = session.execute(
                select(ItemMedia).where(
                    ItemMedia.item_id == item.id,
                    ItemMedia.is_cover
                )
            ).scalar_one_or_none()
            
            # 生成高亮摘要
            highlight = None
            if keyword and item.description:
                desc_lower = item.description.lower()
                kw_lower = keyword.lower()
                if kw_lower in desc_lower:
                    start = max(0, desc_lower.find(kw_lower) - 20)
                    end = min(len(item.description), start + 60)
                    highlight = f"...{item.description[start:end]}..."
                    highlight = highlight.replace(keyword, f"<em>{keyword}</em>")
            
            result_items.append({
                "id": item.id,
                "title": item.title,
                "price": float(item.price),
                "image": cover_image.image_url if cover_image else "",
                "category": cat.name if cat else "未分类",
                "seller_name": seller.username if seller else "未知",
                "seller_avatar": seller.avatar_url if seller else None,
                "view_count": item.view_count or 0,
                "favorite_count": 0,  # 需要关联查询
                "status": item.status,
                "created_at": item.created_at,
                "highlight": highlight
            })
        
        # 保存搜索历史
        if user_id and keyword:
            SearchService.save_search_history(session, user_id, keyword, total)
        
        # 更新热门搜索
        if keyword:
            SearchService.update_trending(session, keyword)
        
        # 相关搜索建议
        suggestions = [
            f"{keyword} 二手",
            f"{keyword} 全新",
            f"{keyword} 配件",
            f"便宜的{keyword}"
        ] if keyword else []
        
        return {
            "items": result_items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "query": keyword,
            "suggestions": suggestions
        }
    
    @staticmethod
    def save_search_history(
        session: Session,
        user_id: int,
        keyword: str,
        result_count: int
    ):
        """保存搜索历史"""
        from apps.core.models import SearchHistory
        
        history = SearchHistory(
            user_id=user_id,
            keyword=keyword,
            result_count=result_count
        )
        session.add(history)
        session.flush()
    
    @staticmethod
    def update_trending(session: Session, keyword: str):
        """更新热门搜索统计"""
        from apps.core.models import SearchTrending
        from datetime import date
        
        today = date.today()
        
        # 查找今天的记录
        trending = session.execute(
            select(SearchTrending).where(
                SearchTrending.keyword == keyword,
                SearchTrending.date == today
            )
        ).scalar_one_or_none()
        
        if trending:
            trending.search_count += 1
            trending.last_searched_at = datetime.utcnow()
        else:
            trending = SearchTrending(
                keyword=keyword,
                search_count=1,
                date=today,
                last_searched_at=datetime.utcnow()
            )
            session.add(trending)
        
        session.flush()
    
    @staticmethod
    def get_autocomplete(
        session: Session,
        query: str,
        limit: int = 10
    ) -> Dict[str, Any]:
        """搜索自动补全"""
        from apps.core.models import Item, Category, SearchTrending
        
        suggestions = []
        
        # 从热门搜索中匹配
        trending = session.execute(
            select(SearchTrending).where(
                SearchTrending.keyword.ilike(f"%{query}%")
            ).order_by(desc(SearchTrending.search_count)).limit(5)
        ).scalars().all()
        
        for t in trending:
            suggestions.append({
                "text": t.keyword,
                "type": "keyword",
                "count": t.search_count
            })
        
        # 从商品标题中匹配
        items = session.execute(
            select(Item.title).where(
                Item.title.ilike(f"%{query}%"),
                Item.status == "available"
            ).distinct().limit(5)
        ).scalars().all()
        
        for title in items:
            if not any(s["text"].lower() == title.lower() for s in suggestions):
                suggestions.append({
                    "text": title,
                    "type": "item",
                    "count": None
                })
        
        # 从分类中匹配
        categories = session.execute(
            select(Category).where(
                Category.name.ilike(f"%{query}%")
            ).limit(3)
        ).scalars().all()
        
        for cat in categories:
            suggestions.append({
                "text": cat.name,
                "type": "category",
                "count": None
            })
        
        return {
            "suggestions": suggestions[:limit],
            "total": len(suggestions)
        }
    
    @staticmethod
    def get_popular_searches(
        session: Session,
        limit: int = 10
    ) -> Dict[str, Any]:
        """获取热门搜索"""
        from apps.core.models import SearchTrending
        from datetime import date, timedelta
        
        # 获取最近7天的热门搜索
        week_ago = date.today() - timedelta(days=7)
        
        # 聚合统计
        trending = session.execute(
            select(
                SearchTrending.keyword,
                func.sum(SearchTrending.search_count).label('total_count')
            ).where(
                SearchTrending.date >= week_ago
            ).group_by(
                SearchTrending.keyword
            ).order_by(
                desc('total_count')
            ).limit(limit)
        ).all()
        
        keywords = []
        for row in trending:
            keywords.append({
                "keyword": row.keyword,
                "count": row.total_count,
                "trend": "stable"  # 简化处理，可以添加趋势计算
            })
        
        return {
            "keywords": keywords,
            "updated_at": datetime.utcnow()
        }
    
    @staticmethod
    def get_search_history(
        session: Session,
        user_id: int,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """获取用户搜索历史"""
        from apps.core.models import SearchHistory
        
        # 查询总数
        total = session.execute(
            select(func.count()).select_from(SearchHistory).where(
                SearchHistory.user_id == user_id
            )
        ).scalar() or 0
        
        # 分页查询
        history = session.execute(
            select(SearchHistory).where(
                SearchHistory.user_id == user_id
            ).order_by(desc(SearchHistory.created_at))
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).scalars().all()
        
        result = []
        for h in history:
            result.append({
                "id": h.id,
                "keyword": h.keyword,
                "searched_at": h.created_at,
                "result_count": h.result_count or 0
            })
        
        return {
            "history": result,
            "total": total
        }
    
    @staticmethod
    def delete_search_history(
        session: Session,
        user_id: int,
        history_id: int
    ) -> Dict[str, Any]:
        """删除单条搜索历史"""
        from apps.core.models import SearchHistory
        
        history = session.execute(
            select(SearchHistory).where(
                SearchHistory.id == history_id,
                SearchHistory.user_id == user_id
            )
        ).scalar_one_or_none()
        
        if not history:
            raise ValueError("搜索历史不存在")
        
        session.delete(history)
        session.flush()
        
        return {"success": True, "message": "搜索历史已删除"}
    
    @staticmethod
    def clear_search_history(
        session: Session,
        user_id: int
    ) -> Dict[str, Any]:
        """清空用户搜索历史"""
        from apps.core.models import SearchHistory
        
        session.execute(
            SearchHistory.__table__.delete().where(
                SearchHistory.user_id == user_id
            )
        )
        session.flush()
        
        return {"success": True, "message": "搜索历史已清空"}
    
    @staticmethod
    def get_search_suggestions(
        session: Session,
        query: str,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """智能搜索建议"""
        from apps.core.models import Category, SearchTrending
        from datetime import date, timedelta
        
        suggestions = {
            "related_searches": [],
            "hot_keywords": [],
            "categories": []
        }
        
        # 相关搜索（基于热门搜索）
        related = session.execute(
            select(SearchTrending.keyword).where(
                SearchTrending.keyword.ilike(f"%{query}%")
            ).order_by(desc(SearchTrending.search_count)).limit(5)
        ).scalars().all()
        suggestions["related_searches"] = list(related)
        
        # 添加一些变体
        if query not in suggestions["related_searches"]:
            suggestions["related_searches"].extend([
                f"{query} 二手",
                f"{query} 全新",
                f"便宜的{query}"
            ])
        
        # 热门关键词
        week_ago = date.today() - timedelta(days=7)
        hot = session.execute(
            select(SearchTrending.keyword).where(
                SearchTrending.date >= week_ago
            ).group_by(SearchTrending.keyword)
            .order_by(desc(func.sum(SearchTrending.search_count)))
            .limit(5)
        ).scalars().all()
        suggestions["hot_keywords"] = list(hot)
        
        # 相关分类
        cats = session.execute(
            select(Category.name).where(
                Category.name.ilike(f"%{query}%")
            ).limit(5)
        ).scalars().all()
        suggestions["categories"] = list(cats)
        
        return suggestions


# 导出所有服务
__all__ = [
    "ItemService",
    "FavoriteService", 
    "CommentService",
    "TransactionService",
    "MessageService",
    "SearchService"
]
