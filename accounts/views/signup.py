import re
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import logout
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.http import HttpRequest, HttpResponse
from ..models import Profile
from .auth import get_client_ip
from ..services.email_verification import send_verification_email, set_email_rate_limit

def signup_view(request: HttpRequest) -> HttpResponse:
    """
    1~2단계: 기본 회원가입 정보(학교 선택, 실명, 학교 이메일, 비밀번호)를 처리하는 뷰.
    이메일 인증 대기 상태(signup_step=3, is_active=False)로 가입을 완료하고 인증 메일을 전송합니다.
    """
    if request.user.is_authenticated:
        # 로그인 상태인데 미완료 가입자인지 먼저 체크
        if hasattr(request.user, 'profile') and request.user.profile.signup_step < 6:
            if request.user.profile.signup_step == 4:
                return redirect('accounts:signup_extra')
            elif request.user.profile.signup_step == 5:
                return redirect('accounts:signup_id_card')
        return redirect('main:index')
        
    if request.method == 'POST':
        school: str = request.POST.get('school', '').strip()
        name: str = request.POST.get('name', '').strip()
        email: str = request.POST.get('email', '').strip()
        password: str = request.POST.get('password', '')
        confirm_password: str = request.POST.get('confirm-password', '')
        terms_age: bool = request.POST.get('terms_age') == 'on'
        terms_service: bool = request.POST.get('terms_service') == 'on'
        terms_privacy: bool = request.POST.get('terms_privacy') == 'on'
        
        # 1. Validation
        if not school or not name or not email or not password or not confirm_password:
            messages.error(request, "모든 필드를 입력해주세요.")
            return render(request, 'accounts/signup.html')
            
        if school != "부산대학교":
            messages.error(request, "현재는 부산대학교 학생만 가입할 수 있습니다.")
            return render(request, 'accounts/signup.html')
            
        if not terms_age or not terms_service or not terms_privacy:
            messages.error(request, "필수 동의 항목에 모두 동의해주세요.")
            return render(request, 'accounts/signup.html')
            
        # Name format validation (prevent script injection & special characters)
        name_regex: str = r'^[a-zA-Z가-힣\s]+$'
        if not re.match(name_regex, name):
            messages.error(request, "이름은 한글, 영문, 공백만 입력할 수 있으며 특수문자나 숫자는 불가능합니다.")
            return render(request, 'accounts/signup.html')
            
        # 2. Strong email format validation
        email_regex: str = r'^[a-zA-Z0-9_.+-]+@pusan\.ac\.kr$'
        if not re.match(email_regex, email, re.IGNORECASE):
            messages.error(request, "부산대학교 이메일(@pusan.ac.kr)만 사용할 수 있습니다.")
            return render(request, 'accounts/signup.html')
            
        # 3. Password strength and match checking
        if password != confirm_password:
            messages.error(request, "비밀번호가 일치하지 않습니다.")
            return render(request, 'accounts/signup.html')
            
        try:
            validate_password(password)
        except ValidationError as e:
            for error in e.messages:
                messages.error(request, error)
            return render(request, 'accounts/signup.html')
            
        # 4. Check for duplicate account
        if User.objects.filter(username=email).exists() or User.objects.filter(email=email).exists():
            messages.error(request, "이미 등록된 이메일 주소입니다.")
            return render(request, 'accounts/signup.html')
            
        # 5. Create user and profile securely under a single transaction
        try:
            with transaction.atomic():
                user: User = User.objects.create_user(
                    username=email,
                    email=email,
                    password=password,
                    first_name=name
                )
                user.is_active = False  # Save in inactive state
                user.save()
                
                # Initial signup_step is set to 3 (Email Verification)
                profile: Profile = Profile.objects.create(
                    user=user,
                    signup_step=3
                )
                profile.save()
                
            # Save the unverified email in the session and redirect to verification page
            request.session['unverified_email'] = email
            
            # Send verification email immediately
            ip: str = get_client_ip(request)
            send_verification_email(request, user)
            set_email_rate_limit(ip, email)
            
            messages.success(request, "회원가입 기본 정보가 등록되었습니다. 인증 메일을 발송했으니 메일함을 확인해 주세요.")
            return redirect('accounts:verification_needed')
            
        except Exception:
            messages.error(request, "회원가입 처리 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.")
            
    return render(request, 'accounts/signup.html')

def signup_extra_view(request: HttpRequest) -> HttpResponse:
    """
    4단계: 이메일 인증을 완료한 유저로부터 학번(입학년도), 나이, 학과를 추가로 기입받는 뷰.
    이 뷰는 로그인되어 있고, signup_step == 4 상태인 유저만 접근 가능합니다.
    """
    if not request.user.is_authenticated:
        messages.error(request, "접근 권한이 없습니다. 먼저 로그인해 주세요.")
        return redirect('accounts:login')
        
    profile: Profile = request.user.profile
    if profile.signup_step != 4:
        if profile.signup_step == 5:
            return redirect('accounts:signup_id_card')
        elif profile.signup_step >= 6:
            return redirect('main:index')
        else:
            logout(request)
            return redirect('accounts:login')
            
    if request.method == 'POST':
        admission_year_raw: str = request.POST.get('admission_year', '').strip()
        age_raw: str = request.POST.get('age', '').strip()
        department: str = request.POST.get('department', '').strip()
        
        # 1. Validation
        if not admission_year_raw or not department or not age_raw:
            messages.error(request, "학번(입학년도), 나이, 학과를 모두 입력해 주세요.")
            return render(request, 'accounts/signup_extra.html')
            
        # 학번(입학년도) 형식 검증 (정수형, 1900년 ~ 현재 연도)
        try:
            admission_year: int = int(admission_year_raw)
            current_year: int = timezone.now().year
            if admission_year < 1900 or admission_year > current_year:
                messages.error(request, f"올바른 입학년도(1900 ~ {current_year})를 입력해 주세요.")
                return render(request, 'accounts/signup_extra.html')
        except ValueError:
            messages.error(request, "입학년도는 숫자 형식이어야 합니다.")
            return render(request, 'accounts/signup_extra.html')
            
        # 나이 검증
        try:
            age: int = int(age_raw)
            if age < 1 or age > 120:
                messages.error(request, "올바른 나이를 입력해주세요. (1 ~ 120)")
                return render(request, 'accounts/signup_extra.html')
        except ValueError:
            messages.error(request, "나이는 숫자 형식이어야 합니다.")
            return render(request, 'accounts/signup_extra.html')
                    
        # 학과 검증 (현재는 "자유전공학부"만 입력 가능)
        if department != "자유전공학부":
            messages.error(request, "현재 가입 가능한 학과는 '자유전공학부'뿐입니다.")
            return render(request, 'accounts/signup_extra.html')
            
        # 2. 프로필 정보 업데이트 및 다음 단계로 변경
        try:
            with transaction.atomic():
                profile.admission_year = admission_year
                profile.age = age
                profile.department = department
                profile.signup_step = 5
                profile.save()
            return redirect('accounts:signup_id_card')
        except Exception:
            messages.error(request, "추가 정보 저장 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.")
            
    return render(request, 'accounts/signup_extra.html')

def signup_id_card_view(request: HttpRequest) -> HttpResponse:
    """
    5단계: 모바일 학생증 인증 안내를 보여주는 뷰. (테스트용 서비스 미구현 안내 포함)
    이 뷰는 로그인되어 있고, signup_step == 5 상태인 유저만 접근 가능합니다.
    """
    if not request.user.is_authenticated:
        messages.error(request, "접근 권한이 없습니다. 먼저 로그인해 주세요.")
        return redirect('accounts:login')
        
    profile: Profile = request.user.profile
    if profile.signup_step != 5:
        if profile.signup_step == 4:
            return redirect('accounts:signup_extra')
        elif profile.signup_step >= 6:
            return redirect('main:index')
        else:
            logout(request)
            return redirect('accounts:login')
            
    if request.method == 'POST':
        try:
            with transaction.atomic():
                profile.signup_step = 6
                profile.save()
            # 세션 정리 및 로그아웃 후 로그인 뷰로 이동
            logout(request)
            messages.success(request, "회원가입 프로세스가 모두 성공적으로 완료되었습니다! 가입하신 정보로 로그인해 주세요.")
            return redirect('accounts:login')
        except Exception:
            messages.error(request, "처리 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.")
            
    return render(request, 'accounts/signup_id_card.html')

def terms_view(request: HttpRequest) -> HttpResponse:
    """
    이용약관 페이지를 렌더링합니다.
    """
    return render(request, 'accounts/terms.html')

def privacy_view(request: HttpRequest) -> HttpResponse:
    """
    개인정보처리방침 페이지를 렌더링합니다.
    """
    return render(request, 'accounts/privacy.html')
