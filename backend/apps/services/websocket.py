"""
WebSocket服务 - 实时通知推送
"""
from typing import Dict, Set
from datetime import datetime
import json

from fastapi import WebSocket, WebSocketDisconnect, APIRouter
from loguru import logger


router = APIRouter(prefix="/ws", tags=["WebSocket"])


class ConnectionManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        # 存储活跃连接：{user_id: {websocket1, websocket2, ...}}
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        
    async def connect(self, websocket: WebSocket, user_id: int):
        """接受新连接"""
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        
        self.active_connections[user_id].add(websocket)
        logger.info(f"User {user_id} connected. Total connections: {len(self.active_connections[user_id])}")
        
        # 发送欢迎消息
        await self.send_personal_message({
            "type": "system",
            "message": "连接成功",
            "timestamp": datetime.utcnow().isoformat()
        }, websocket)
    
    def disconnect(self, websocket: WebSocket, user_id: int):
        """断开连接"""
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            
            # 如果用户没有其他连接，删除该用户
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
            
            logger.info(f"User {user_id} disconnected")
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """发送消息到指定连接"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Failed to send message: {str(e)}")
    
    async def send_to_user(self, user_id: int, message: dict):
        """发送消息到指定用户的所有连接"""
        if user_id in self.active_connections:
            disconnected = set()
            
            for websocket in self.active_connections[user_id]:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Failed to send to user {user_id}: {str(e)}")
                    disconnected.add(websocket)
            
            # 清理断开的连接
            for websocket in disconnected:
                self.disconnect(websocket, user_id)
    
    async def broadcast(self, message: dict, exclude_user: int = None):
        """广播消息到所有用户"""
        for user_id, connections in self.active_connections.items():
            if exclude_user and user_id == exclude_user:
                continue
            
            await self.send_to_user(user_id, message)
    
    def is_user_online(self, user_id: int) -> bool:
        """检查用户是否在线"""
        return user_id in self.active_connections and len(self.active_connections[user_id]) > 0
    
    def get_online_users(self) -> list[int]:
        """获取所有在线用户ID"""
        return list(self.active_connections.keys())


# 全局连接管理器
manager = ConnectionManager()


@router.websocket("/notifications/{user_id}")
async def websocket_notifications(websocket: WebSocket, user_id: int):
    """
    WebSocket通知端点
    
    连接URL: ws://localhost:8000/api/v1/ws/notifications/{user_id}
    """
    await manager.connect(websocket, user_id)
    
    try:
        while True:
            # 接收客户端消息
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                message_type = message.get("type")
                
                # 处理心跳
                if message_type == "ping":
                    await manager.send_personal_message({
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    }, websocket)
                
                # 处理在线状态查询
                elif message_type == "check_online":
                    target_user_id = message.get("user_id")
                    is_online = manager.is_user_online(target_user_id)
                    await manager.send_personal_message({
                        "type": "online_status",
                        "user_id": target_user_id,
                        "online": is_online,
                        "timestamp": datetime.utcnow().isoformat()
                    }, websocket)
                
                # 其他消息类型
                else:
                    logger.info(f"Received message from user {user_id}: {message}")
                    
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON from user {user_id}: {data}")
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
        logger.info(f"User {user_id} disconnected normally")
    
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {str(e)}")
        manager.disconnect(websocket, user_id)


# 通知发送函数（供其他模块调用）

async def send_notification(user_id: int, notification: dict):
    """
    发送通知到指定用户
    
    Args:
        user_id: 目标用户ID
        notification: 通知内容
            {
                "type": "new_message" | "new_order" | "new_comment" | "system",
                "title": "通知标题",
                "content": "通知内容",
                "link": "/messages/123",  # 可选
                "data": {...}  # 可选的额外数据
            }
    """
    notification["timestamp"] = datetime.utcnow().isoformat()
    notification["read"] = False
    notification["id"] = f"{user_id}_{int(datetime.utcnow().timestamp() * 1000)}"
    
    await manager.send_to_user(user_id, notification)
    logger.info(f"Notification sent to user {user_id}: {notification.get('title')}")


async def broadcast_notification(notification: dict, exclude_user: int = None):
    """
    广播通知到所有在线用户
    
    Args:
        notification: 通知内容
        exclude_user: 排除的用户ID（可选）
    """
    notification["timestamp"] = datetime.utcnow().isoformat()
    notification["read"] = False
    
    await manager.broadcast(notification, exclude_user)
    logger.info(f"Notification broadcasted: {notification.get('title')}")


async def notify_new_message(sender_id: int, receiver_id: int, message_content: str):
    """发送新消息通知"""
    await send_notification(receiver_id, {
        "type": "new_message",
        "title": "新消息",
        "content": message_content[:50] + ("..." if len(message_content) > 50 else ""),
        "link": f"/messages?userId={sender_id}",
        "data": {
            "sender_id": sender_id,
            "message": message_content
        }
    })


async def notify_new_order(seller_id: int, buyer_id: int, order_id: int, item_title: str):
    """发送新订单通知"""
    await send_notification(seller_id, {
        "type": "new_order",
        "title": "新订单",
        "content": f"您有一个新订单：{item_title}",
        "link": f"/orders?id={order_id}",
        "data": {
            "buyer_id": buyer_id,
            "order_id": order_id,
            "item_title": item_title
        }
    })


async def notify_order_status_change(user_id: int, order_id: int, status: str, item_title: str):
    """发送订单状态变更通知"""
    status_text = {
        "paid": "已支付",
        "shipped": "已发货",
        "completed": "已完成",
        "cancelled": "已取消",
        "refunded": "已退款"
    }.get(status, status)
    
    await send_notification(user_id, {
        "type": "order_update",
        "title": "订单状态更新",
        "content": f"订单「{item_title}」状态已更新为：{status_text}",
        "link": f"/orders?id={order_id}",
        "data": {
            "order_id": order_id,
            "status": status
        }
    })


async def notify_new_comment(seller_id: int, commenter_id: int, item_id: int, item_title: str, rating: int):
    """发送新评论通知"""
    await send_notification(seller_id, {
        "type": "new_comment",
        "title": "新评价",
        "content": f"您的商品「{item_title}」收到了{rating}星评价",
        "link": f"/item/{item_id}",
        "data": {
            "commenter_id": commenter_id,
            "item_id": item_id,
            "rating": rating
        }
    })


async def notify_item_favorited(seller_id: int, user_id: int, item_id: int, item_title: str):
    """发送商品被收藏通知"""
    await send_notification(seller_id, {
        "type": "item_favorited",
        "title": "商品被收藏",
        "content": f"您的商品「{item_title}」被收藏了",
        "link": f"/item/{item_id}",
        "data": {
            "user_id": user_id,
            "item_id": item_id
        }
    })


async def send_system_notification(notification: dict):
    """发送系统通知到所有用户"""
    notification["type"] = "system"
    await broadcast_notification(notification)
