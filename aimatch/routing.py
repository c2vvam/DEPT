from django.urls import path
from django.urls.resolvers import URLPattern
from typing import List
from . import consumers

websocket_urlpatterns: List[URLPattern] = [
    path('ws/waiting-room/<int:group_id>/', consumers.WaitingRoomConsumer.as_asgi()),
    path('ws/chat/<int:group_id>/', consumers.ChatConsumer.as_asgi()),
]

