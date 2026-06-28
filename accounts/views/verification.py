from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib import messages
from django.db import transaction
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.http import HttpRequest, HttpResponse

from .auth import get_client_ip
from ..services.email_verification import (
    email_verification_token_generator,
    send_verification_email,
    check_email_rate_limit,
    set_email_rate_limit
)

def verification_needed_view(request: HttpRequest) -> HttpResponse:
    """
    View displaying the registration verification status/resend page.
    Retrieves the email directly from the session instead of user input.
    """
    if request.user.is_authenticated:
        return redirect('main:index')
        
    email: str | None = request.session.get('unverified_email')
    if not email:
        messages.warning(request, "인증을 진행할 이메일 정보가 없습니다. 다시 로그인해 주세요.")
        return redirect('accounts:login')
        
    if request.method == 'POST':
        ip: str = get_client_ip(request)
        
        # Look up user by email from session
        user: User | None = User.objects.filter(email=email).first()
        
        if user:
            if not user.is_active:
                is_allowed, error_msg = check_email_rate_limit(ip, email)
                if is_allowed:
                    try:
                        send_verification_email(request, user)
                        set_email_rate_limit(ip, email)
                        messages.success(request, "인증 메일을 발송했습니다. 메일함을 확인해주세요.")
                    except Exception:
                        messages.error(request, "인증 메일 전송 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.")
                else:
                    messages.error(request, error_msg)
            else:
                messages.info(request, "이미 인증이 완료된 계정입니다. 로그인해주세요.")
                return redirect('accounts:login')
        else:
            messages.error(request, "가입 정보가 유효하지 않습니다. 다시 회원가입을 진행해주세요.")
            return redirect('accounts:signup')
            
    return render(request, 'accounts/resend_verification.html', {'email': email})

def verify_email_view(request: HttpRequest, uidb64: str, token: str) -> HttpResponse:
    """
    URL target for the one-time verification links.
    Validates user pk and token, and activates the account if valid.
    Transitions to step 4, logs the user in, and redirects to extra info collection.
    """
    user: User | None = None
    try:
        uid: str = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
        
    if user is None:
        messages.error(request, "유효하지 않은 인증 링크입니다.")
        return redirect('accounts:login')
        
    if user.is_active:
        # If active but signup_step is incomplete, let login_view handle redirection
        # Or redirect them directly if we can log them in or they are already logged in
        if hasattr(user, 'profile') and user.profile.signup_step < 6:
            messages.info(request, "이미 이메일 인증이 완료되었습니다. 나머지 가입 절차를 진행해 주세요.")
            if user.profile.signup_step == 4:
                return redirect('accounts:signup_extra')
            elif user.profile.signup_step == 5:
                return redirect('accounts:signup_id_card')
        messages.info(request, "이미 인증이 완료된 계정입니다. 로그인해주세요.")
        return redirect('accounts:login')
        
    # Verify token
    if email_verification_token_generator.check_token(user, token):
        try:
            with transaction.atomic():
                user.is_active = True
                user.save()
                profile = user.profile
                profile.signup_step = 4
                profile.save()
            # Clean up the session data to prevent Session Pollution
            request.session.pop('unverified_email', None)
            
            # Log the user in to proceed with signup steps
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            
            messages.success(request, "이메일 인증이 완료되었습니다! 추가 정보를 입력해 주세요.")
            return redirect('accounts:signup_extra')
        except Exception:
            messages.error(request, "이메일 인증 처리 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.")
            return redirect('accounts:verification_needed')
    else:
        messages.error(request, "인증 링크가 만료되었거나 유효하지 않습니다. 다시 인증 메일을 발송해주세요.")
        return redirect('accounts:verification_needed')
