from channels.generic.websocket import WebsocketConsumer
import json
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from asgiref.sync import async_to_sync
from .models import *


class ChatRoomConsumer(WebsocketConsumer):

    def connect(self):
        self.user = self.scope["user"]
        self.chatroom_name = self.scope['url_route']['kwargs']['chatroom_name']
        self.chatroom = get_object_or_404(ChatGroup, group_name=self.chatroom_name)

        async_to_sync(self.channel_layer.group_add)(
            self.chatroom_name,
            self.channel_name
        )

        if self.user.is_authenticated:
            self.chatroom.users_online.remove(self.user)
            self.chatroom.users_online.add(self.user)
            self.update_online_count()

        self.accept()

    def disconnect(self, close_code):
        if self.user.is_authenticated:
            self.chatroom.users_online.remove(self.user)

        try:
            self.send_typing_indicator(is_typing=False)
        except Exception:
            pass

        async_to_sync(self.channel_layer.group_discard)(
            self.chatroom_name,
            self.channel_name
        )

        if self.user.is_authenticated:
            self.update_online_count()

    def receive(self, text_data):
        data = json.loads(text_data)

        # Typing indicator
        if 'typing' in data:
            self.send_typing_indicator(is_typing=data['typing'])
            return

        # Message delete
        if data.get('type') == 'delete_message':
            message_id = data.get('message_id')
            try:
                message = GroupMessage.objects.get(id=message_id)
                if self.user == message.author or self.user == self.chatroom.admin:
                    message.delete()
                    # Broadcast delete to all users
                    async_to_sync(self.channel_layer.group_send)(
                        self.chatroom_name,
                        {
                            "type": "delete_handler",
                            "message_id": message_id,
                        }
                    )
            except GroupMessage.DoesNotExist:
                pass
            return

        body = data.get('body', '').strip()
        if not body:
            return

        message = GroupMessage.objects.create(
            body=body,
            author=self.user,
            group=self.chatroom,
        )

        async_to_sync(self.channel_layer.group_send)(
            self.chatroom_name,
            {
                "type": "message_handler",
                "message_id": message.id,
            }
        )

        self.send_typing_indicator(is_typing=False)

    def message_handler(self, event):
        message = GroupMessage.objects.get(id=event["message_id"])
        html = render_to_string(
            "partials/chat_message_p.html",
            {"message": message, "user": self.user}
        )
        self.send(text_data=html)

    def delete_handler(self, event):
        # Send delete signal to all connected users
        self.send(text_data=json.dumps({
            "type": "delete_message",
            "message_id": event["message_id"],
        }))

    def send_typing_indicator(self, is_typing):
        async_to_sync(self.channel_layer.group_send)(
            self.chatroom_name,
            {
                "type": "typing_handler",
                "is_typing": is_typing,
                "username": self.user.username,
                "name": self.user.profile.name if hasattr(self.user, 'profile') else self.user.username,
                "avatar": str(self.user.profile.avatar) if hasattr(self.user, 'profile') and self.user.profile.avatar else '',
            }
        )

    def typing_handler(self, event):
        if event["username"] == self.user.username:
            return
        html = render_to_string(
            "partials/typing_indicator.html",
            {
                "is_typing": event["is_typing"],
                "username": event["username"],
                "name": event["name"],
                "avatar": event["avatar"],
            }
        )
        self.send(text_data=html)

    def update_online_count(self):
        count = self.chatroom.users_online.count()
        is_online = self.user in self.chatroom.users_online.all()

        async_to_sync(self.channel_layer.group_send)(
            self.chatroom_name,
            {
                "type": "online_count_handler",
                "online_count": count,
                "changed_user_id": self.user.id,
                "is_online": is_online,
            }
        )

    def online_count_handler(self, event):
        html = render_to_string(
            "partials/online_count.html",
            {"online_count": event["online_count"]}
        )
        self.send(text_data=html)

        self.send(text_data=json.dumps({
            "type": "user_online_status",
            "user_id": event["changed_user_id"],
            "is_online": event["is_online"],
        }))