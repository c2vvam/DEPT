from django.contrib import admin
from .models import Need, Group, GroupMember, Notification

@admin.register(Need)
class NeedAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'type', 'size_category', 'status', 'created_at')
    list_filter = ('type', 'size_category', 'status')
    search_fields = ('user__username', 'detail_text')
    ordering = ('-created_at',)


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'type', 'size_category', 'status', 'created_at', 'min_reached_at')
    list_filter = ('type', 'size_category', 'status')
    search_fields = ('title', 'tags')
    ordering = ('-created_at',)


@admin.register(GroupMember)
class GroupMemberAdmin(admin.ModelAdmin):
    list_display = ('id', 'group', 'user', 'joined_at')
    list_filter = ('group__type', 'group__status')
    search_fields = ('group__title', 'user__username')
    ordering = ('-joined_at',)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'message', 'is_read', 'created_at')
    list_filter = ('is_read',)
    search_fields = ('user__username', 'message')
    ordering = ('-created_at',)
