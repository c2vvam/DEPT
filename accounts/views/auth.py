from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.cache import cache
from django.utils.http import url_has_allowed_host_and_scheme
from django.conf import settings
from django.http import HttpRequest, HttpResponse
from accounts.backends import AllowInactiveUserModelBackend

def get_client_ip(request: HttpRequest) -> str:
    """
    Get the client's real IP address from metadata, handling proxies.
    """
    x_forwarded_for: str | None = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip: str = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '')
    return ip

def check_rate_limit(ip: str, email: str) -> tuple[bool, str | None]:
    """
    Check if either the IP address or the email address has exceeded the rate limit.
    Max 5 attempts in 5 minutes.
    """
    ip_key: str = f"login_attempts_ip:{ip}"
    email_key: str = f"login_attempts_email:{email}"
    
    ip_attempts: int = cache.get(ip_key, 0)
    email_attempts: int = cache.get(email_key, 0)
    
    if ip_attempts >= 5 or email_attempts >= 5:
        return False, "너무 많은 로그인 시도가 발생했습니다. 잠시 후 다시 시도해 주세요. (5분 제한)"
    return True, None

def increment_rate_limit(ip: str, email: str) -> None:
    """
    Increment login failure attempts for both IP and email. Set expiry to 5 minutes (300s).
    """
    ip_key: str = f"login_attempts_ip:{ip}"
    email_key: str = f"login_attempts_email:{email}"
    
    ip_attempts: int = cache.get(ip_key, 0) + 1
    email_attempts: int = cache.get(email_key, 0) + 1
    
    cache.set(ip_key, ip_attempts, 300)
    cache.set(email_key, email_attempts, 300)

def clear_rate_limit(ip: str, email: str) -> None:
    """
    Clear login failure tracking upon successful login.
    """
    ip_key: str = f"login_attempts_ip:{ip}"
    email_key: str = f"login_attempts_email:{email}"
    cache.delete(ip_key)
    cache.delete(email_key)

def login_view(request: HttpRequest) -> HttpResponse:
    """
    Secure login view with CSRF validation, session rotation, rate limiting, and redirect safety.
    Redirects to email verification page if user credentials are correct but the email is not verified (inactive status).
    """
    # Clean up residual password reset credentials on entering login page (Fixes vulnerability 4)
    request.session.pop('pwd_reset_token', None)
    request.session.pop('pwd_reset_verified_email', None)
    request.session.pop('pwd_reset_change_attempts', None)
    
    if request.user.is_authenticated:
        return redirect('main:index')
        
    if request.method == 'POST':
        email: str = request.POST.get('email', '').strip()
        password: str = request.POST.get('password', '')
        remember_me: bool = request.POST.get('remember_me') == 'on'
        
        # 1. Verify inputs are present
        if not email or not password:
            messages.error(request, "이메일과 비밀번호를 모두 입력해주세요.")
            return render(request, 'accounts/login.html')
            
        ip: str = get_client_ip(request)
        
        # 2. Check rate limiter
        is_allowed, error_msg = check_rate_limit(ip, email)
        if not is_allowed:
            messages.error(request, error_msg)
            return render(request, 'accounts/login.html')
            
        # 3. Authenticate user using email as username
        # Instantiate the backend directly to support inactive user authentication without registering it globally
        backend = AllowInactiveUserModelBackend()
        user = backend.authenticate(request, username=email, password=password)
        
        if user is not None:
            if user.is_active:
                # Login successful: create session (rotates session key internally)
                # Explicitly record the standard backend in session to avoid lookup failure
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                clear_rate_limit(ip, email)
                
                # Clean up unverified_email if it exists in session
                request.session.pop('unverified_email', None)
                
                # Control session lifecycle based on Remember Me option
                if remember_me:
                    # Keep session active for 2 weeks
                    request.session.set_expiry(1209600)
                else:
                    # Expire session when browser closes
                    request.session.set_expiry(0)
                    
                # Check signup_step for incomplete registration
                if hasattr(user, 'profile') and user.profile.signup_step < 6:
                    messages.info(request, "회원가입의 남은 단계를 완료해 주세요.")
                    if user.profile.signup_step == 4:
                        return redirect('accounts:signup_extra')
                    elif user.profile.signup_step == 5:
                        return redirect('accounts:signup_id_card')
                    
                # Prevent Open Redirect attacks by validating the 'next' parameter
                redirect_to: str = request.POST.get('next', request.GET.get('next', ''))
                
                allowed_hosts: set[str] = set(settings.ALLOWED_HOSTS)
                if settings.DEBUG:
                    allowed_hosts.add(request.get_host())
                    
                url_is_safe: bool = url_has_allowed_host_and_scheme(
                    url=redirect_to,
                    allowed_hosts=allowed_hosts,
                    require_https=request.is_secure(),
                )
                if not url_is_safe or not redirect_to:
                    redirect_to = 'main:index'
                    
                return redirect(redirect_to)
            else:
                # User exists, is inactive (unverified), and password is correct.
                # Save the unverified email in the session
                request.session['unverified_email'] = user.email
                messages.info(request, "이메일 인증이 완료되지 않았습니다. 인증 메일을 발송하여 계정을 활성화해주세요.")
                return redirect('accounts:verification_needed')
        else:
            # Login failed: increment counters and display non-revealing error
            increment_rate_limit(ip, email)
            messages.error(request, "이메일 또는 비밀번호가 올바르지 않습니다.")
            
    return render(request, 'accounts/login.html')

def logout_view(request: HttpRequest) -> HttpResponse:
    """
    Secure logout view to invalidate user session and clear session cookies.
    """
    if request.user.is_authenticated:
        logout(request)
    return redirect('main:index')
