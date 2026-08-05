import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import User

from .models import Message


class DirectMessageConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope.get('user')
        if not user or not user.is_authenticated:
            await self.close(code=4401)
            return

        self.user = user
        self.user_group = f'dm_{self.user.id}'
        await self.channel_layer.group_add(self.user_group, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'user_group'):
            await self.channel_layer.group_discard(self.user_group, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        if not text_data:
            return

        try:
            payload = json.loads(text_data)
        except json.JSONDecodeError:
            return

        event_kind = payload.get('kind', 'chat.message')

        if event_kind == 'chat.typing':
            receiver_id = payload.get('receiver_id')
            is_typing = bool(payload.get('is_typing'))
            try:
                receiver_id = int(receiver_id)
            except (TypeError, ValueError):
                return

            typing_payload = {
                'type': 'chat.typing',
                'typing': {
                    'sender_id': self.user.id,
                    'sender_username': self.user.username,
                    'receiver_id': receiver_id,
                    'is_typing': is_typing,
                },
            }
            await self.channel_layer.group_send(f'dm_{receiver_id}', {'type': 'message_event', 'payload': typing_payload})
            return

        if event_kind == 'chat.read':
            contact_id = payload.get('contact_id')
            try:
                contact_id = int(contact_id)
            except (TypeError, ValueError):
                return
            updated_count = await self._mark_messages_read(contact_id=contact_id)
            read_payload = {
                'type': 'chat.read',
                'read': {
                    'reader_id': self.user.id,
                    'contact_id': contact_id,
                    'updated_count': updated_count,
                },
            }
            await self.channel_layer.group_send(f'dm_{contact_id}', {'type': 'message_event', 'payload': read_payload})
            await self.channel_layer.group_send(f'dm_{self.user.id}', {'type': 'message_event', 'payload': read_payload})
            return

        content = (payload.get('content') or '').strip()
        receiver_id = payload.get('receiver_id')

        if not content or not receiver_id:
            return

        message = await self._create_message(receiver_id=receiver_id, content=content)
        if not message:
            return

        event_payload = {
            'type': 'chat.message',
            'message': {
                'id': message.id,
                'sender_id': message.sender_id,
                'sender_username': message.sender.username,
                'receiver_id': message.receiver_id,
                'receiver_username': message.receiver.username,
                'content': message.content,
                'is_read': message.is_read,
                'created_at': message.created_at.isoformat(),
            },
        }

        await self.channel_layer.group_send(f'dm_{message.receiver_id}', {'type': 'message_event', 'payload': event_payload})
        await self.channel_layer.group_send(f'dm_{message.sender_id}', {'type': 'message_event', 'payload': event_payload})

    async def message_event(self, event):
        await self.send(text_data=json.dumps(event['payload']))

    @database_sync_to_async
    def _create_message(self, receiver_id, content):
        try:
            receiver = User.objects.get(pk=receiver_id)
        except User.DoesNotExist:
            return None

        return Message.objects.create(
            sender=self.user,
            receiver=receiver,
            content=content,
        )

    @database_sync_to_async
    def _mark_messages_read(self, contact_id):
        return Message.objects.filter(
            sender_id=contact_id,
            receiver=self.user,
            is_read=False,
        ).update(is_read=True)
