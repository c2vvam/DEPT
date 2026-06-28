from django.urls import path
from . import views

app_name = 'aimatch'

urlpatterns = [
    path('', views.matching_board_view, name='matching'),
    path('api/user-status', views.user_status_view, name='user_status'),
    path('needs', views.needs_create_view, name='needs_create'),
    path('needs/<int:need_id>/match-result', views.needs_match_result_view, name='needs_match_result'),
    path('needs/<int:need_id>/accept-group', views.needs_accept_group_view, name='needs_accept_group'),
    path('needs/<int:need_id>/decline-group', views.needs_decline_group_view, name='needs_decline_group'),
    path('groups', views.groups_list_view, name='groups_list'),
    path('groups/<int:group_id>', views.groups_detail_view, name='groups_detail'),
    path('groups/<int:group_id>/join', views.groups_join_view, name='groups_join'),
    path('groups/<int:group_id>/leave', views.groups_leave_view, name='groups_leave'),
    path('groups/<int:group_id>/messages', views.chat_history_view, name='chat_history'),
    path('api/notifications', views.notifications_list_view, name='notifications_list'),
    path('api/notifications/read', views.notifications_mark_read_view, name='notifications_mark_read'),
]
