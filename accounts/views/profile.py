import re
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash, logout as auth_logout
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.db import transaction
from django.contrib.auth.models import User
from django.http import HttpRequest, HttpResponse
from ..models import Profile

@login_required
def profile_view(request: HttpRequest) -> HttpResponse:
    """
    Secure profile view to read user profile information.
    Prevents editing critical attributes as per security requirements.
    """
    user: User = request.user
    profile: Profile
    profile, _ = Profile.objects.get_or_create(user=user)
    
    if request.method == 'POST':
        messages.error(request, "이름과 나이는 수정할 수 없는 고유 인증 정보입니다.")
        return redirect('accounts:profile')
            
    return render(request, 'accounts/profile.html', {'profile': profile})

@login_required
def password_change_view(request: HttpRequest) -> HttpResponse:
    """
    Secure password change view.
    Requires current password validation to prevent session hijacking attacks.
    """
    user: User = request.user
    
    if request.method == 'POST':
        current_password: str = request.POST.get('current_password', '')
        new_password: str = request.POST.get('new_password', '')
        confirm_new_password: str = request.POST.get('confirm_new_password', '')
        
        # 1. Validation
        if not current_password or not new_password or not confirm_new_password:
            messages.error(request, "모든 비밀번호 필드를 입력해주세요.")
            return render(request, 'accounts/password_change.html')
            
        # 2. Verify current password
        if not user.check_password(current_password):
            messages.error(request, "현재 비밀번호가 올바르지 않습니다.")
            return render(request, 'accounts/password_change.html')
            
        # 3. Verify new password strength and match
        if new_password == current_password:
            messages.error(request, "새 비밀번호는 현재 비밀번호와 다르게 설정해야 합니다.")
            return render(request, 'accounts/password_change.html')
            
        if new_password != confirm_new_password:
            messages.error(request, "새 비밀번호 확인이 일치하지 않습니다.")
            return render(request, 'accounts/password_change.html')
            
        try:
            validate_password(new_password, user=user)
        except ValidationError as e:
            for error in e.messages:
                messages.error(request, error)
            return render(request, 'accounts/password_change.html')
            
        # 4. Update password securely
        try:
            user.set_password(new_password)
            user.save()
            
            # Update session hash to keep the current user logged in after password change
            update_session_auth_hash(request, user)
            
            messages.success(request, "비밀번호가 성공적으로 변경되었습니다.")
            return redirect('accounts:profile')
        except Exception:
            messages.error(request, "비밀번호 변경 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.")
            
    return render(request, 'accounts/password_change.html')

@login_required
def withdraw_view(request: HttpRequest) -> HttpResponse:
    """
    Secure user withdrawal/account deletion view.
    Requires password verification to protect against account destruction.
    Includes rate-limiting on password verification failures to prevent brute-force attacks within active sessions.
    """
    user: User = request.user
    
    # 1. Check if the user has exceeded password validation limits
    attempts: int = request.session.get('withdraw_attempts', 0)
    if attempts >= 5:
        auth_logout(request)
        messages.error(request, "비밀번호 입력 오류 횟수가 초과되어 계정 보호를 위해 강제 로그아웃 처리되었습니다.")
        return redirect('accounts:login')
        
    if request.method == 'POST':
        password: str = request.POST.get('password', '')
        
        # 2. Validation
        if not password:
            messages.error(request, "비밀번호를 입력해주세요.")
            return render(request, 'accounts/withdraw.html')
            
        # 3. Verify password
        if not user.check_password(password):
            attempts += 1
            request.session['withdraw_attempts'] = attempts
            if attempts >= 5:
                auth_logout(request)
                messages.error(request, "비밀번호 입력 오류 횟수가 초과되어 계정 보호를 위해 강제 로그아웃 처리되었습니다.")
                return redirect('accounts:login')
                
            messages.error(request, f"입력하신 비밀번호가 올바르지 않습니다. (실패 횟수: {attempts}/5)")
            return render(request, 'accounts/withdraw.html')
            
        # 4. Delete user and log out
        try:
            with transaction.atomic():
                user.delete()
            request.session.pop('withdraw_attempts', None)
            auth_logout(request)
            messages.success(request, "회원 탈퇴가 성공적으로 완료되었습니다. 그동안 이용해 주셔서 감사합니다.")
            return redirect('main:index')
        except Exception:
            messages.error(request, "회원 탈퇴 처리 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.")
            
    return render(request, 'accounts/withdraw.html')
