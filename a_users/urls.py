from django.urls import path
from a_users.views import *

urlpatterns = [
    path('', profile_view, name="profile"),
    path('edit/', profile_edit_view, name="profile-edit"),
    path('onboarding/', profile_edit_view, name="profile-onboarding"),
    path('settings/', profile_settings_view, name="profile-settings"),
    path('emailchange/', profile_emailchange, name="profile-emailchange"),
    path('usernamechange/', profile_usernamechange, name="profile-usernamechange"),
    path('emailverify/', profile_emailverify, name="profile-emailverify"),
    path('delete/', profile_delete_view, name="profile-delete"),
    path('friends/', friends_list_view, name="friends-list"),
    path('friend-requests/', friend_requests_view, name="friend-requests"),
    path('friend/request/<username>/', send_friend_request, name="send-friend-request"),
    path('friend/handle/<int:request_id>/<str:action>/', handle_friend_request, name="handle-friend-request"),
    path('friend/remove/<username>/', remove_friend, name="remove-friend"),
]