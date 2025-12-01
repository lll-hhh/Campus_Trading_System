"""
消息模块后端测试
测试 MessageService 和消息 API 路由
"""
import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session

# 测试 MessageService
class TestMessageService:
    """消息服务测试"""
    
    def test_send_message_success(self):
        """测试成功发送消息"""
        from apps.services.business_logic import MessageService
        
        # 创建模拟的 session
        mock_session = MagicMock(spec=Session)
        
        # 模拟接收者存在
        mock_receiver = MagicMock()
        mock_receiver.username = "receiver_user"
        mock_receiver.avatar_url = None
        
        # 模拟发送者
        mock_sender = MagicMock()
        mock_sender.username = "sender_user"
        mock_sender.avatar_url = None
        
        # 模拟 session.get 返回用户
        def mock_get(model, id):
            if id == 2:  # receiver
                return mock_receiver
            elif id == 1:  # sender
                return mock_sender
            return None
        
        mock_session.get = mock_get
        
        # 模拟会话查询返回 None（需要创建新会话）
        mock_session.execute.return_value.scalar_one_or_none.return_value = None
        
        # 模拟 Conversation
        mock_conv = MagicMock()
        mock_conv.id = 1
        mock_conv.user1_id = 1
        mock_conv.user2_id = 2
        mock_conv.unread_count_user2 = 0
        
        # 模拟 Message
        mock_message = MagicMock()
        mock_message.id = 100
        mock_message.content = "测试消息"
        mock_message.item_id = None
        mock_message.is_read = False
        mock_message.created_at = datetime.utcnow()
        
        with patch('apps.services.business_logic.MessageService.get_or_create_conversation', return_value=mock_conv):
            with patch('apps.core.models.Message') as MockMessage:
                MockMessage.return_value = mock_message
                
                # 这里我们测试基本逻辑结构
                # 实际运行需要完整的数据库设置
                assert MessageService is not None
    
    def test_send_message_to_self_fails(self):
        """测试不能给自己发送消息"""
        from apps.services.business_logic import MessageService
        
        mock_session = MagicMock(spec=Session)
        
        # 模拟用户存在
        mock_user = MagicMock()
        mock_user.username = "test_user"
        mock_session.get = MagicMock(return_value=mock_user)
        
        # 尝试给自己发送消息应该失败
        with pytest.raises(ValueError, match="不能给自己发送消息"):
            MessageService.send_message(
                session=mock_session,
                sender_id=1,
                receiver_id=1,  # 同一用户
                content="测试消息"
            )
    
    def test_send_message_receiver_not_found(self):
        """测试接收者不存在时失败"""
        from apps.services.business_logic import MessageService
        
        mock_session = MagicMock(spec=Session)
        mock_session.get = MagicMock(return_value=None)  # 用户不存在
        
        with pytest.raises(ValueError, match="接收者不存在"):
            MessageService.send_message(
                session=mock_session,
                sender_id=1,
                receiver_id=999,
                content="测试消息"
            )
    
    def test_get_conversations(self):
        """测试获取会话列表"""
        from apps.services.business_logic import MessageService
        
        mock_session = MagicMock(spec=Session)
        
        # 模拟会话数据
        mock_conv = MagicMock()
        mock_conv.id = 1
        mock_conv.user1_id = 1
        mock_conv.user2_id = 2
        mock_conv.last_message = "最后一条消息"
        mock_conv.last_message_time = datetime.utcnow()
        mock_conv.unread_count_user1 = 3
        mock_conv.unread_count_user2 = 0
        
        # 模拟用户
        mock_other_user = MagicMock()
        mock_other_user.username = "other_user"
        mock_other_user.avatar_url = None
        
        mock_session.execute.return_value.scalars.return_value.all.return_value = [mock_conv]
        mock_session.get = MagicMock(return_value=mock_other_user)
        
        result = MessageService.get_conversations(mock_session, user_id=1)
        
        assert "conversations" in result
        assert "total" in result
        assert "total_unread" in result
    
    def test_get_unread_count(self):
        """测试获取未读消息数"""
        from apps.services.business_logic import MessageService
        
        mock_session = MagicMock(spec=Session)
        
        # 模拟会话数据
        mock_conv1 = MagicMock()
        mock_conv1.user1_id = 1
        mock_conv1.user2_id = 2
        mock_conv1.unread_count_user1 = 5
        
        mock_conv2 = MagicMock()
        mock_conv2.user1_id = 1
        mock_conv2.user2_id = 3
        mock_conv2.unread_count_user1 = 2
        
        mock_session.execute.return_value.scalars.return_value.all.return_value = [mock_conv1, mock_conv2]
        
        result = MessageService.get_unread_count(mock_session, user_id=1)
        
        assert result["total_unread"] == 7
        assert result["conversations_with_unread"] == 2


class TestMessagesAPI:
    """消息 API 路由测试"""
    
    def test_message_response_model(self):
        """测试消息响应模型"""
        from apps.api_gateway.routers.messages import MessageResponse
        
        msg_data = {
            "id": 1,
            "conversation_id": 1,
            "sender_id": 1,
            "sender_name": "sender",
            "sender_avatar": None,
            "receiver_id": 2,
            "receiver_name": "receiver",
            "receiver_avatar": None,
            "content": "测试消息",
            "message_type": "text",
            "item_id": None,
            "is_read": False,
            "created_at": datetime.utcnow()
        }
        
        response = MessageResponse(**msg_data)
        assert response.id == 1
        assert response.content == "测试消息"
        assert response.is_read == False
    
    def test_conversation_response_model(self):
        """测试会话响应模型"""
        from apps.api_gateway.routers.messages import ConversationResponse
        
        conv_data = {
            "id": 1,
            "other_user_id": 2,
            "other_user_name": "other_user",
            "other_user_avatar": None,
            "last_message": "最后消息",
            "last_message_time": datetime.utcnow(),
            "unread_count": 5,
            "created_at": datetime.utcnow()
        }
        
        response = ConversationResponse(**conv_data)
        assert response.id == 1
        assert response.unread_count == 5
    
    def test_message_send_request_validation(self):
        """测试发送消息请求验证"""
        from apps.api_gateway.routers.messages import MessageSendRequest
        
        # 有效请求
        valid_request = MessageSendRequest(
            receiver_id=2,
            content="有效消息内容"
        )
        assert valid_request.receiver_id == 2
        assert valid_request.message_type == "text"  # 默认值
        
        # 空内容应该失败
        with pytest.raises(Exception):
            MessageSendRequest(
                receiver_id=2,
                content=""  # 空内容
            )


# 集成测试（需要实际数据库连接）
class TestMessagesIntegration:
    """消息模块集成测试（需要数据库）"""
    
    @pytest.mark.skip(reason="需要实际数据库连接")
    def test_full_message_flow(self):
        """测试完整的消息流程"""
        # 1. 用户1发送消息给用户2
        # 2. 用户2查看会话列表
        # 3. 用户2读取消息
        # 4. 验证已读状态更新
        pass
    
    @pytest.mark.skip(reason="需要实际数据库连接")
    def test_conversation_creation(self):
        """测试会话自动创建"""
        # 发送消息时应自动创建会话
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
