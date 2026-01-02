
import sys
import os
from sqlalchemy import select
from datetime import datetime

# Add backend to path
sys.path.append('/mnt/data/桌面/newkeshe2/backend')

from apps.core.database import db_manager
from apps.services.business_logic import MessageService
from apps.core.models import User, Message, Conversation

def test_get_messages():
    with db_manager.session_scope() as session:
        # Find a user with messages
        user = session.execute(select(User).limit(1)).scalar()
        if not user:
            print("No users found")
            return
        
        print(f"Testing for user: {user.username} (id: {user.id})")
        
        # Get conversations
        convs = MessageService.get_conversations(session, user.id)
        print(f"Found {len(convs['conversations'])} conversations")
        
        if convs['conversations']:
            conv_id = convs['conversations'][0]['id']
            print(f"Getting messages for conversation: {conv_id}")
            
            messages_data = MessageService.get_conversation_messages(session, user.id, conv_id)
            print(f"Found {len(messages_data['messages'])} messages")
            if messages_data['messages']:
                print("First message sample:")
                print(messages_data['messages'][0])

if __name__ == "__main__":
    test_get_messages()
