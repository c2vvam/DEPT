import secrets
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.signing import TimestampSigner, SignatureExpired, BadSignature
from django.utils.crypto import constant_time_compare
from django.conf import settings
from django.http import HttpRequest, HttpResponse
from .auth import get_client_ip

def check_password_reset_rate_limit(ip: str, email: str) -> tuple[bool, str | None]:
    """
    Check if the user/IP has exceeded the password reset email request limits.
    Limit: 1 request per minute per email, and 5 requests per hour per IP.
    Ensures email key is lowercased.
    """
    email_key: str = f"pwd_reset_limit_email:{email.lower()}"
    ip_key: str = f"pwd_reset_limit_ip:{ip}"
    
    if cache.get(email_key):
        return False, "이미 비밀번호 재설정 이메일이 발송되었습니다. 1분 후에 다시 시도해주세요."
        
    ip_attempts: int = cache.get(ip_key, 0)
    if ip_attempts >= 5:
        return False, "단기간에 너무 많은 비밀번호 재설정 요청이 있었습니다. 잠시 후 다시 시도해주세요. (IP 제한)"
        
    return True, None

def set_password_reset_rate_limit(ip: str, email: str) -> None:
    """
    Set cache indicators to enforce email rate limits for password resets.
    Ensures email key is lowercased.
    """
    email_key: str = f"pwd_reset_limit_email:{email.lower()}"
    ip_key: str = f"pwd_reset_limit_ip:{ip}"
    
    # 1 minute lock for this email
    cache.set(email_key, True, 60)
    
    # IP limit increment (expires in 1 hour / 3600 seconds)
    ip_attempts: int = cache.get(ip_key, 0) + 1
    cache.set(ip_key, ip_attempts, 3600)

def find_password_view(request: HttpRequest) -> HttpResponse:
    """
    Handles the first step of resetting password: Email verification request.
    Protects against email enumeration by showing a generic success message even if email is not found.
    Normalizes email to lower case to prevent rate-limit bypasses.
    Uses CSPRNG (secrets module) to generate OTP code.
    """
    if request.user.is_authenticated:
        return redirect('main:index')
        
    if request.method == 'POST':
        # Normalizing to lower case (Fixes vulnerability 2)
        email: str = request.POST.get('email', '').strip().lower()
        if not email:
            messages.error(request, "이메일 주소를 입력해주세요.")
            return render(request, 'accounts/find_password.html')
            
        # Enforce email domain restriction
        if not email.endswith('@pusan.ac.kr'):
            messages.error(request, "부산대학교 이메일 주소만 사용 가능합니다. (example@pusan.ac.kr)")
            return render(request, 'accounts/find_password.html')
            
        ip: str = get_client_ip(request)
        
        # Check rate limiter
        is_allowed, error_msg = check_password_reset_rate_limit(ip, email)
        if not is_allowed:
            messages.error(request, error_msg or "요청 제한을 초과했습니다.")
            return render(request, 'accounts/find_password.html')
            
        # Generate 6-digit code using CSPRNG (Fixes vulnerability 3)
        code: int = secrets.SystemRandom().randint(100000, 999999)
        code_str: str = str(code)
        
        # Save code to cache (expires in 5 minutes)
        code_key: str = f"pwd_reset_code:{email}"
        attempts_key: str = f"pwd_reset_attempts:{email}"
        cache.set(code_key, code_str, 300)
        cache.set(attempts_key, 0, 300)
        
        # Set rate limit
        set_password_reset_rate_limit(ip, email)
        
        # Save reset email in session for stage 2
        request.session['pwd_reset_email'] = email
        
        # Lookup user
        user: User | None = User.objects.filter(email=email, is_active=True).first()
        
        # Username Enumeration Mitigation (Fixes vulnerability 1):
        # Even if user doesn't exist, we behave identically to prevent leaks.
        if user:
            # Send email
            subject: str = "[dept] 비밀번호 재설정 인증번호입니다."
            message: str = f"""안녕하세요, {user.first_name}님.
dept 계정의 비밀번호 재설정을 위해 아래 인증번호를 입력해주세요:

인증번호: {code_str}

이 인증번호는 5분 동안 유효합니다.
본인이 요청한 것이 아니라면 이 메일을 무시하셔도 됩니다.

감사합니다.
dept 팀
"""
            if settings.DEBUG:
                print("\n" + "="*80)
                print(f"[DEBUG PASSWORD RESET] To: {email}")
                print(f"[DEBUG PASSWORD RESET] Code: {code_str}")
                print("="*80 + "\n")
                
            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=False,
                )
            except Exception:
                messages.error(request, "인증 메일 전송 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.")
                return render(request, 'accounts/find_password.html')
        else:
            # If user does not exist, we just simulate work and print code in DEBUG console
            if settings.DEBUG:
                print("\n" + "="*80)
                print(f"[DEBUG PASSWORD RESET - USER NOT FOUND] Simulated To: {email}")
                print(f"[DEBUG PASSWORD RESET - USER NOT FOUND] Code: {code_str}")
                print("="*80 + "\n")

        # Identical success message and redirection
        messages.success(request, "인증 코드가 이메일로 발송되었습니다. 5분 이내에 코드를 입력해주세요.")
        return redirect('accounts:find_password_verify_code')
            
    return render(request, 'accounts/find_password.html')

def find_password_verify_code_view(request: HttpRequest) -> HttpResponse:
    """
    Handles step 2: Verification of the 6-digit code.
    Enforces lockout after 5 failed attempts using constant-time comparison.
    Generates a secure timestamped token on success.
    """
    if request.user.is_authenticated:
        return redirect('main:index')
        
    email: str | None = request.session.get('pwd_reset_email')
    if not email:
        messages.warning(request, "비밀번호 재설정 프로세스가 유효하지 않습니다. 다시 이메일을 입력해주세요.")
        return redirect('accounts:find_password')
        
    # Ensure email normalization
    email = email.strip().lower()
        
    if request.method == 'POST':
        code_input: str = request.POST.get('code', '').strip()
        if not code_input:
            messages.error(request, "인증 코드를 입력해주세요.")
            return render(request, 'accounts/find_password_verify.html', {'email': email})
            
        code_key: str = f"pwd_reset_code:{email}"
        attempts_key: str = f"pwd_reset_attempts:{email}"
        
        attempts: int = cache.get(attempts_key, 0)
        if attempts >= 5:
            # Lockout: invalidate session reset state
            request.session.pop('pwd_reset_email', None)
            cache.delete(code_key)
            cache.delete(attempts_key)
            messages.error(request, "인증 시도 횟수(5회)를 초과했습니다. 처음부터 다시 시도해주세요.")
            return redirect('accounts:find_password')
            
        cached_code: str | None = cache.get(code_key)
        
        if not cached_code:
            messages.error(request, "인증 코드가 만료되었거나 존재하지 않습니다. 다시 요청해주세요.")
            return render(request, 'accounts/find_password_verify.html', {'email': email})
            
        # Constant-time comparison to prevent timing attacks
        if constant_time_compare(cached_code, code_input):
            # Success: clean up verification caches
            cache.delete(code_key)
            cache.delete(attempts_key)
            
            # Generate a secure timestamp signer token (valid for 10 minutes)
            signer: TimestampSigner = TimestampSigner()
            token: str = signer.sign(email)
            
            request.session['pwd_reset_token'] = token
            request.session['pwd_reset_verified_email'] = email
            request.session['pwd_reset_change_attempts'] = 0  # To limit password change retry attempts
            request.session.pop('pwd_reset_email', None)
            
            messages.success(request, "이메일 인증이 완료되었습니다. 새 비밀번호를 입력해주세요.")
            return redirect('accounts:find_password_reset')
        else:
            # Increment failed attempts count
            attempts += 1
            cache.set(attempts_key, attempts, 300)
            
            if attempts >= 5:
                request.session.pop('pwd_reset_email', None)
                cache.delete(code_key)
                cache.delete(attempts_key)
                messages.error(request, "인증 시도 횟수를 초과했습니다. 처음부터 다시 시도해주세요.")
                return redirect('accounts:find_password')
                
            messages.error(request, f"올바르지 않은 인증 코드입니다. (실패 횟수: {attempts}/5)")
            return render(request, 'accounts/find_password_verify.html', {'email': email})
            
    return render(request, 'accounts/find_password_verify.html', {'email': email})

def find_password_reset_view(request: HttpRequest) -> HttpResponse:
    """
    Handles step 3: Inputting the new password.
    Validates token presence, token timestamp, validates strength,
    updates user password, and flushes session (lifecycle revocation).
    Limits failed change attempts to 3 to prevent brute forcing and residual token lifetime.
    """
    if request.user.is_authenticated:
        return redirect('main:index')
        
    token: str | None = request.session.get('pwd_reset_token')
    email: str | None = request.session.get('pwd_reset_verified_email')
    
    if not token or not email:
        messages.warning(request, "비밀번호 재설정 프로세스가 유효하지 않습니다. 다시 시도해주세요.")
        return redirect('accounts:find_password')
        
    # Ensure normalization
    email = email.strip().lower()
        
    # Validate token signature and age (max 10 minutes / 600s)
    signer: TimestampSigner = TimestampSigner()
    try:
        unsigned_email: str = signer.unsign(token, max_age=600)
        # Verify the signed email matches session email to prevent token reuse across emails
        if unsigned_email != email:
            raise BadSignature("Email mismatch")
    except (SignatureExpired, BadSignature):
        request.session.pop('pwd_reset_token', None)
        request.session.pop('pwd_reset_verified_email', None)
        request.session.pop('pwd_reset_change_attempts', None)
        messages.error(request, "비밀번호 재설정 세션이 만료되었거나 유효하지 않습니다. 다시 시도해 주세요.")
        return redirect('accounts:find_password')
        
    if request.method == 'POST':
        # Limit retry attempts for password changes to prevent residual token misuse (Fixes vulnerability 4)
        change_attempts: int = request.session.get('pwd_reset_change_attempts', 0)
        if change_attempts >= 3:
            request.session.pop('pwd_reset_token', None)
            request.session.pop('pwd_reset_verified_email', None)
            request.session.pop('pwd_reset_change_attempts', None)
            messages.error(request, "비밀번호 변경 입력 오류 횟수를 초과했습니다. 다시 인증해주세요.")
            return redirect('accounts:find_password')

        new_password: str = request.POST.get('new_password', '')
        confirm_new_password: str = request.POST.get('confirm_new_password', '')
        
        if not new_password or not confirm_new_password:
            messages.error(request, "새 비밀번호와 비밀번호 확인을 모두 입력해 주세요.")
            return render(request, 'accounts/find_password_reset.html')
            
        if new_password != confirm_new_password:
            # Increment validation failure attempt
            request.session['pwd_reset_change_attempts'] = change_attempts + 1
            messages.error(request, "새 비밀번호가 일치하지 않습니다.")
            return render(request, 'accounts/find_password_reset.html')
            
        user: User | None = User.objects.filter(email=email, is_active=True).first()
        if not user:
            # Fallback mitigation if user was deleted or disabled during the process
            request.session.pop('pwd_reset_token', None)
            request.session.pop('pwd_reset_verified_email', None)
            request.session.pop('pwd_reset_change_attempts', None)
            messages.error(request, "계정을 찾을 수 없습니다. 다시 시도해 주세요.")
            return redirect('accounts:find_password')
            
        # Validate password strength against Django settings validators
        try:
            validate_password(new_password, user=user)
        except ValidationError as e:
            request.session['pwd_reset_change_attempts'] = change_attempts + 1
            for error in e.messages:
                messages.error(request, error)
            return render(request, 'accounts/find_password_reset.html')
            
        # Update password
        try:
            user.set_password(new_password)
            user.save()
            
            # Session lifecycle revocation: Invalidate all sessions by flushing.
            request.session.flush()
            
            messages.success(request, "비밀번호가 성공적으로 변경되었습니다. 새로운 비밀번호로 로그인해주세요.")
            return redirect('accounts:login')
        except Exception:
            messages.error(request, "비밀번호 설정 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.")
            return render(request, 'accounts/find_password_reset.html')
            
    return render(request, 'accounts/find_password_reset.html')
