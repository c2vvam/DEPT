from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.auth.models import User
from django.http import HttpRequest
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured

class EmailVerificationTokenGenerator(PasswordResetTokenGenerator):
    """
    Custom token generator that generates a secure, one-time link.
    By including is_active in the hash value, the token becomes invalid
    as soon as the user is activated, ensuring true one-time use.
    """
    def _make_hash_value(self, user: User, timestamp: int) -> str:
        return (
            str(user.pk) + 
            str(timestamp) + 
            str(user.is_active) + 
            str(user.password)
        )

email_verification_token_generator = EmailVerificationTokenGenerator()

def generate_verification_url(request: HttpRequest, user: User) -> str:
    """
    Generate a secure verification URL for the user.
    Uses SITE_URL from settings to prevent Host header injection.
    """
    uid: str = urlsafe_base64_encode(force_bytes(user.pk))
    token: str = email_verification_token_generator.make_token(user)
    
    path: str = reverse('accounts:verify_email', kwargs={'uidb64': uid, 'token': token})
    site_url: str | None = getattr(settings, 'SITE_URL', None)
    
    # Force SITE_URL to prevent Host header injection
    if not site_url:
        if settings.DEBUG:
            site_url = "http://127.0.0.1:8000"
        else:
            raise ImproperlyConfigured("SITE_URL settings is required in production environment to prevent Host Header Injection.")
            
    return f"{site_url.rstrip('/')}{path}"


def check_email_rate_limit(ip: str, email: str) -> tuple[bool, str | None]:
    """
    Check if the user/IP has exceeded email sending limits.
    Limit: 1 email per minute per email address, and 5 emails per hour per IP.
    """
    email_key: str = f"email_verify_limit_email:{email}"
    ip_key: str = f"email_verify_limit_ip:{ip}"
    
    if cache.get(email_key):
        return False, "인증 메일이 이미 발송되었습니다. 1분 후에 다시 시도해주세요."
        
    ip_attempts: int = cache.get(ip_key, 0)
    if ip_attempts >= 5:
        return False, "단기간에 너무 많은 인증 메일 발송 요청이 있었습니다. 잠시 후 다시 시도해주세요. (IP 제한)"
        
    return True, None

def set_email_rate_limit(ip: str, email: str) -> None:
    """
    Set cache indicators to enforce email rate limits.
    """
    email_key: str = f"email_verify_limit_email:{email}"
    ip_key: str = f"email_verify_limit_ip:{ip}"
    
    # 1 minute lock for this email
    cache.set(email_key, True, 60)
    
    # IP limit increment (expires in 1 hour / 3600 seconds)
    ip_attempts: int = cache.get(ip_key, 0) + 1
    cache.set(ip_key, ip_attempts, 3600)

def send_verification_email(request: HttpRequest, user: User) -> None:
    """
    Send the verification email containing the one-time link.
    """
    verify_url: str = generate_verification_url(request, user)
    
    subject: str = "[dept] 회원가입 이메일 인증을 완료해주세요."
    
    message: str = f"""안녕하세요, {user.first_name}님.
dept 회원가입을 감사드립니다.

아래 링크를 클릭하여 이메일 인증을 완료하고 계정을 활성화해주세요:
{verify_url}

이 링크는 일회성 링크이며, 24시간 동안 유효합니다.
본인이 가입한 것이 아니라면 이 메일을 무시하셔도 됩니다.

감사합니다.
dept 팀
"""
    
    # Print clean plain text link to console for easy copy-pasting during local development
    if settings.DEBUG:
        print("\n" + "="*80)
        print(f"[DEBUG EMAIL] To: {user.email}")
        print(f"[DEBUG EMAIL] Verification Link: {verify_url}")
        print("="*80 + "\n")
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )
