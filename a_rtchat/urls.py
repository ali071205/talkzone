from django.urls import path
from . import views

urlpatterns = [
    path('', views.chat_view, name='home'),
    path('chat/create-group/', views.create_groupchat, name='create-groupchat'),
    path('chat/search/', views.search_groups, name='search-groups'),
    path('chat/notifications/', views.notifications_view, name='notifications'),
    path('chat/room/<chatroom_name>/', views.chat_view, name='chat-room'),
    path('chat/invite/<invite_token>/', views.groupchat_invite, name='groupchat-invite'),
    path('chat/join-sent/<chatroom_name>/', views.join_request_sent, name='join-request-sent'),
    path('chat/group/<chatroom_name>/edit/', views.groupchat_edit, name='groupchat-edit'),
    path('chat/group/<chatroom_name>/delete/', views.groupchat_delete, name='groupchat-delete'),
    path('chat/group/<chatroom_name>/leave/', views.groupchat_leave, name='groupchat-leave'),
    path('chat/group/<chatroom_name>/join-request/', views.send_join_request, name='send-join-request'),
    path('chat/join-request/<int:request_id>/<str:action>/', views.handle_join_request, name='handle-join-request'),
    path('chat/message/<int:message_id>/delete/', views.delete_message, name='delete-message'),
    path('chat/message/<int:message_id>/react/', views.toggle_reaction, name='toggle-reaction'),
    path('chat/room/<chatroom_name>/upload/', views.upload_file, name='upload-file'),
    path('chat/room/<chatroom_name>/bot/', views.bot_reply, name='bot-reply'),
    path('chat/<username>/', views.get_create_chatroom, name='start-chat'),
]