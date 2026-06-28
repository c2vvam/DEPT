import json
import time
from typing import Any, Dict
from django.contrib.auth.models import User
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import GroupMember, ChatMessage

class WaitingRoomConsumer(AsyncWebsocketConsumer):
    group_id: int
    room_group_name: str

    @database_sync_to_async
    def is_member(self, user: User, group_id: int) -> bool:
        if not user.is_authenticated:
            return False
        return GroupMember.objects.filter(group_id=group_id, user=user).exists()

    async def connect(self) -> None:
        self.group_id = int(self.scope['url_route']['kwargs']['group_id'])
        self.room_group_name = f"waiting_room_{self.group_id}"
        user = self.scope['user']

        if not await self.is_member(user, self.group_id):
            await self.close()
            return

        # Join room group
        if self.channel_layer is not None:
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )

        await self.accept()

    async def disconnect(self, close_code: int) -> None:
        # Leave room group
        if hasattr(self, 'room_group_name') and self.channel_layer is not None:
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data: str) -> None:
        pass

    async def waiting_room_message(self, event: Dict[str, Any]) -> None:
        message: str = event.get('message', 'update')

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'waiting_room_update',
            'message': message
        }))


class ChatConsumer(AsyncWebsocketConsumer):
    group_id: int
    room_group_name: str
    last_sent_time: float

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.last_sent_time = 0.0

    @database_sync_to_async
    def is_member(self, user: User, group_id: int) -> bool:
        if not user.is_authenticated:
            return False
        return GroupMember.objects.filter(group_id=group_id, user=user).exists()

    @database_sync_to_async
    def save_message(self, user: User, group_id: int, content: str) -> Dict[str, Any]:
        msg = ChatMessage.objects.create(group_id=group_id, sender=user, content=content)
        profile = user.profile
        real_nickname = profile.nickname if profile.nickname else user.username
        name = user.first_name if user.first_name else real_nickname
        admission_year_text = f"{str(profile.admission_year)[2:]}학번" if profile.admission_year else ""
        return {
            "id": msg.id,
            "sender_id": user.id,
            "sender_name": name,
            "sender_dept": profile.department,
            "sender_year": admission_year_text,
            "content": msg.content,
            "created_at": msg.created_at.isoformat()
        }

    async def connect(self) -> None:
        self.group_id = int(self.scope['url_route']['kwargs']['group_id'])
        self.room_group_name = f"chat_{self.group_id}"
        user = self.scope['user']

        if not await self.is_member(user, self.group_id):
            await self.close()
            return

        if self.channel_layer is not None:
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )

        await self.accept()

    async def disconnect(self, close_code: int) -> None:
        if hasattr(self, 'room_group_name') and self.channel_layer is not None:
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data: str) -> None:
        now = time.time()
        if now - self.last_sent_time < 0.3:
            return
        self.last_sent_time = now

        user = self.scope['user']
        if not await self.is_member(user, self.group_id):
            await self.close()
            return

        try:
            data = json.loads(text_data)
            content = data.get('content', '').strip()
        except json.JSONDecodeError:
            return

        if not content or len(content) > 150:
            return

        msg_data = await self.save_message(user, self.group_id, content)

        if self.channel_layer is not None:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': msg_data
                }
            )

    async def chat_message(self, event: Dict[str, Any]) -> None:
        message = event['message']

        await self.send(text_data=json.dumps({
            'type': 'chat_message_received',
            'message': message
        }))

