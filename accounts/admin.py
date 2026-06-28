from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Profile

# 기본 User 모델 admin 등록 해제 (중복 등록 방지)
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = '프로필 정보'

@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    """
    Custom User Admin profile to show dept user accounts clearly.
    """
    inlines = (ProfileInline,)
    
    # 1. 관리자 유저 목록에서 한눈에 보여줄 컬럼 정의
    list_display = ('username', 'email', 'first_name', 'is_staff', 'is_active', 'date_joined')
    
    # 2. 우측 사이드바 필터 항목
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined')
    
    # 3. 검색 창에서 검색 가능한 속성들 (이메일, 이름 등으로 검색 지원)
    search_fields = ('username', 'email', 'first_name')
    
    # 4. 정렬 방식 정의 (최신 가입자 순으로 배치)
    ordering = ('-date_joined',)

