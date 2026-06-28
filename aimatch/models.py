from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Need(models.Model):
    TYPE_CHOICES = [
        ('friend', '친구찾기'),
        ('study', '스터디'),
        ('project', '프로젝트'),
    ]
    SIZE_CHOICES = [
        ('small', '적음'),
        ('medium', '중간'),
        ('large', '많음'),
    ]
    STATUS_CHOICES = [
        ('pending_matching', '매칭 중'),
        ('matched_waiting', '선택지 대기'),
        ('registered', '매칭 대기 등록'),
        ('matched', '매칭 성사 완료'),
        ('expired', '만료'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='needs')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    detail_text = models.TextField()
    size_category = models.CharField(max_length=20, choices=SIZE_CHOICES)
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default='pending_matching'
    )
    recommended_groups = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.user.username} - {self.get_type_display()} ({self.status})"


class Group(models.Model):
    TYPE_CHOICES = [
        ('friend', '친구찾기'),
        ('study', '스터디'),
        ('project', '프로젝트'),
    ]
    SIZE_CHOICES = [
        ('small', '적음'),
        ('medium', '중간'),
        ('large', '많음'),
    ]
    STATUS_CHOICES = [
        ('forming', 'forming'),
        ('min_reached_grace', 'min_reached_grace'),
        ('confirmed', 'confirmed'),
        ('closed_timeout', 'closed_timeout'),
    ]

    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    size_category = models.CharField(max_length=20, choices=SIZE_CHOICES)
    title = models.CharField(max_length=20)
    tags = models.CharField(max_length=255, default='', blank=True)
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default='forming'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    min_reached_at = models.DateTimeField(null=True, blank=True)
    last_member_change_at = models.DateTimeField(default=timezone.now)

    @property
    def min_size(self) -> int:
        if self.size_category == 'small':
            return 2
        elif self.size_category == 'medium':
            return 5
        elif self.size_category == 'large':
            return 8
        return 2

    @property
    def max_size(self) -> int:
        if self.size_category == 'small':
            return 4
        elif self.size_category == 'medium':
            return 7
        elif self.size_category == 'large':
            return 15
        return 4

    def __str__(self) -> str:
        return f"[{self.get_type_display()}] {self.title} ({self.status})"


class GroupMember(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='group_memberships')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('group', 'user')

    def __str__(self) -> str:
        return f"{self.user.username} in {self.group.title}"


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Notification for {self.user.username}: {self.message[:20]}"


class ChatMessage(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='chat_messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_messages')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.sender.username} in Group {self.group.id}: {self.content[:20]}"

