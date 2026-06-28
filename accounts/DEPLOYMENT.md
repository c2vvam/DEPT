# Accounts 서비스 배포 가이드 (Deployment Guide)

이 문서는 `accounts` 앱(회원가입, 로그인, 비밀번호 재설정 등)의 기능을 실제 운영(Production) 환경에 배포할 때 필수적으로 검토하고 설정해야 하는 보안 및 인프라 구성을 정리한 가이드라인입니다.

---

## 1. 이메일 발송(SMTP) 및 환경 변수 설정

개발 환경(`DEBUG = True`)에서는 이메일이 실제 전송되지 않고 콘솔 터미널에 출력이 되도록 처리되어 있으나, 운영 환경(`DEBUG = False`)에서는 실제로 사용자에게 인증 링크 및 비밀번호 재설정 코드를 메일로 발송해야 합니다.

### Django Settings 설정 (`config/settings.py`)
운영 환경을 위해 아래와 같이 SMTP 관련 백엔드를 설정합니다. 비밀번호나 API 키 등의 민감 정보는 절대 소스코드에 하드코딩하지 않고 환경 변수(`.env` 등)로부터 로드해야 합니다 (`security.md` 제3조 준수).

```python
import os

# 운영 환경에서만 실제 이메일 전송 활성화
if not DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
    EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
    EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True') == 'True'
    EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')       # 발송자 이메일 계정
    EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD') # 비밀번호 또는 앱 비밀번호
    DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER)
else:
    # 로컬 개발 환경용 콘솔 백엔드
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

---

## 2. 호스트 헤더 인젝션 방지 (`SITE_URL` 설정)

이메일 인증 링크 등 절대 경로 생성이 필요한 로직에서는 HTTP 요청의 Host 헤더(`request.get_host()`)를 무조건 신뢰하지 않고, 사전에 검증된 서버 호스트 설정(`SITE_URL`)을 사용하도록 구현되어 있습니다.

### 환경 변수에 설정 추가
배포하는 환경에 맞춰 `.env` 파일 등에 도메인 주소를 설정해야 합니다. 프로덕션 환경에서 이 값이 누락되면 `ImproperlyConfigured` 에러가 발생합니다.

```env
# 운영 서버의 대표 주소 (Trailing Slash 제외)
SITE_URL=https://creditcampus.pusan.ac.kr
```

---

## 3. Rate Limit 및 Lockout용 Redis 캐시 설정

로그인 실패 횟수 제한, 이메일 전송 제한(1분 1회), 비밀번호 재설정 인증 시도(5회 실패 시 락아웃) 등을 관리하기 위해 메모리 캐시보다 성능이 좋고 다중 컨테이너 환경에서도 데이터가 유실되지 않는 **Redis** 등의 분산 캐시 사용을 권장합니다.

### Django Cache 설정
```python
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
```

### Redis 연동 보안 주의사항 (`security.md` 제9조 준수)
1. **패스워드 설정**: `requirepass` 설정을 활성화하여 Redis에 대한 무단 액세스를 차단합니다.
2. **포트 외부 노출 차단**: `docker-compose.yml` 등에서 Redis 포트(`6379`)를 외부에 바인딩하지 않고 오직 장고 백엔드 컨테이너만 내부 Docker 네트워크를 통해 통신하도록 격리합니다.

---

## 4. HTTPS 및 세션 쿠키 보안 강화

사용자의 자격 증명 정보(로그인 비밀번호, 재설정 세션 정보 등)가 네트워크 상에서 탈취되는 것을 방지하기 위해 HTTPS 프로토콜 사용이 강제되어야 합니다.

운영 환경 설정파일에 아래 보안 관련 설정을 필히 추가하십시오 (`security.md` 제8조 준수):

```python
if not DEBUG:
    # 1. 모든 HTTP 요청을 HTTPS로 강제 리다이렉트
    SECURE_SSL_REDIRECT = True
    
    # 2. HTTP Strict Transport Security(HSTS) 설정
    SECURE_HSTS_SECONDS = 31536000  # 1년
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    
    # 3. 세션 및 CSRF 쿠키 보안 설정 (HTTPS 연결 상에서만 쿠키 전송)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    
    # 4. 브라우저 XSS 보호 활성화 및 Iframe 렌더링 방지
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_FRAME_DENY = True
    
    # 5. 프록시 헤더 설정 (Nginx 등의 리버스 프록시 뒤에 있을 경우)
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
```

---

## 5. 배포 전 체크리스트 (Summary Checklist)

- [ ] `.env` 파일에 `SITE_URL`이 명확한 HTTPS 도메인으로 설정되어 있는가?
- [ ] SMTP 서버 정보 및 자격 증명 환경 변수(`EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`)가 안전하게 제공되었는가?
- [ ] Redis 등 캐시 저장소가 암호 인증을 활성화하고 인트라넷 환경에 안전하게 구성되었는가?
- [ ] `DEBUG = False` 환경에서 `ALLOWED_HOSTS`에 실제 도메인이 명시되어 있는가?
- [ ] 세션 쿠키 및 CSRF 쿠키에 `Secure` 플래그 설정이 적용되었는가?
