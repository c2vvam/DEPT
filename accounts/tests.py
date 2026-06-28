from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.core import mail
from django.core.cache import cache
from accounts.models import Profile
from accounts.services.email_verification import email_verification_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.messages import get_messages

class EmailVerificationTests(TestCase):
    def setUp(self) -> None:
        self.client: Client = Client()
        cache.clear()
        
    def test_signup_creates_inactive_user_and_sends_email(self) -> None:
        signup_url: str = reverse('accounts:signup')
        post_data: dict[str, str] = {
            'school': '부산대학교',
            'name': '홍길동',
            'email': 'gildong@pusan.ac.kr',
            'password': 'PnuCreditCampus123!',
            'confirm-password': 'PnuCreditCampus123!',
            'terms_age': 'on',
            'terms_service': 'on',
            'terms_privacy': 'on',
        }
        
        response = self.client.post(signup_url, post_data)
        
        self.assertRedirects(response, reverse('accounts:verification_needed'))
        
        user: User = User.objects.get(email='gildong@pusan.ac.kr')
        self.assertFalse(user.is_active)
        
        profile: Profile = Profile.objects.get(user=user)
        self.assertIsNone(profile.age)
        self.assertEqual(profile.signup_step, 3)
        
        self.assertEqual(self.client.session.get('unverified_email'), 'gildong@pusan.ac.kr')
        
        self.assertEqual(len(mail.outbox), 1)
        
    def test_login_unverified_user_redirects_and_sends_email(self) -> None:
        user: User = User.objects.create_user(
            username='inactive@pusan.ac.kr',
            email='inactive@pusan.ac.kr',
            password='Password123',
            first_name='미인증'
        )
        user.is_active = False
        user.save()
        Profile.objects.create(user=user, age=22, signup_step=3)
        
        login_url: str = reverse('accounts:login')
        
        mail.outbox = []
        
        response = self.client.post(login_url, {
            'email': 'inactive@pusan.ac.kr',
            'password': 'Password123'
        })
        
        self.assertRedirects(response, reverse('accounts:verification_needed'))
        
        self.assertEqual(self.client.session.get('unverified_email'), 'inactive@pusan.ac.kr')
        
        self.assertEqual(len(mail.outbox), 0)
        
        msgs = list(get_messages(response.wsgi_request))
        self.assertTrue(any("이메일 인증이 완료되지 않았습니다" in m.message for m in msgs))
        
        mail.outbox = []
        cache.clear()
        
        session = self.client.session
        session.pop('unverified_email', None)
        session.save()
        
        response_wrong = self.client.post(login_url, {
            'email': 'inactive@pusan.ac.kr',
            'password': 'WrongPassword'
        })
        self.assertEqual(response_wrong.status_code, 200)
        self.assertEqual(len(mail.outbox), 0)
        self.assertIsNone(self.client.session.get('unverified_email'))
        
        msgs_wrong = list(get_messages(response_wrong.wsgi_request))
        self.assertTrue(any("이메일 또는 비밀번호가 올바르지 않습니다" in m.message for m in msgs_wrong))

    def test_email_verification_success(self) -> None:
        user: User = User.objects.create_user(
            username='verify@pusan.ac.kr',
            email='verify@pusan.ac.kr',
            password='Password123',
            first_name='인증대상'
        )
        user.is_active = False
        user.save()
        Profile.objects.create(user=user, signup_step=3)
        
        uid: str = urlsafe_base64_encode(force_bytes(user.pk))
        token: str = email_verification_token_generator.make_token(user)
        
        verify_url: str = reverse('accounts:verify_email', kwargs={'uidb64': uid, 'token': token})
        
        response = self.client.get(verify_url)
        self.assertRedirects(response, reverse('accounts:signup_extra'))
        
        user.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertEqual(user.profile.signup_step, 4)
        
        user.profile.signup_step = 6
        user.profile.save()
        self.client.logout()
        response_retry = self.client.get(verify_url)
        self.assertRedirects(response_retry, reverse('accounts:login'))
        
        msgs = list(get_messages(response_retry.wsgi_request))
        self.assertTrue(any("이미 인증이 완료된 계정입니다" in m.message for m in msgs))
        
    def test_email_verification_invalid_token(self) -> None:
        user: User = User.objects.create_user(
            username='invalidtoken@pusan.ac.kr',
            email='invalidtoken@pusan.ac.kr',
            password='Password123',
            first_name='미인증'
        )
        user.is_active = False
        user.save()
        Profile.objects.create(user=user, signup_step=3)
        
        uid: str = urlsafe_base64_encode(force_bytes(user.pk))
        invalid_token: str = 'invalid-token-12345'
        
        session = self.client.session
        session['unverified_email'] = 'invalidtoken@pusan.ac.kr'
        session.save()
        
        verify_url: str = reverse('accounts:verify_email', kwargs={'uidb64': uid, 'token': invalid_token})
        response = self.client.get(verify_url)
        self.assertRedirects(response, reverse('accounts:verification_needed'))
        
    def test_email_sending_rate_limit(self) -> None:
        user: User = User.objects.create_user(
            username='ratelimit@pusan.ac.kr',
            email='ratelimit@pusan.ac.kr',
            password='Password123',
            first_name='제한대상'
        )
        user.is_active = False
        user.save()
        Profile.objects.create(user=user, signup_step=3)
        
        resend_url: str = reverse('accounts:verification_needed')
        
        session = self.client.session
        session['unverified_email'] = 'ratelimit@pusan.ac.kr'
        session.save()
        
        response1 = self.client.post(resend_url)
        self.assertEqual(len(mail.outbox), 1)
        
        msgs1 = list(get_messages(response1.wsgi_request))
        self.assertTrue(any("인증 메일을 발송했습니다" in m.message for m in msgs1))
        
        mail.outbox = []
        response2 = self.client.post(resend_url)
        self.assertEqual(len(mail.outbox), 0)
        
        msgs2 = list(get_messages(response2.wsgi_request))
        self.assertTrue(any("1분 후에 다시 시도해주세요" in m.message for m in msgs2))


class ProfileAndPasswordTests(TestCase):
    def setUp(self) -> None:
        self.client: Client = Client()
        self.user: User = User.objects.create_user(
            username='testuser@pusan.ac.kr',
            email='testuser@pusan.ac.kr',
            password='OldPassword123',
            first_name='홍길동'
        )
        self.user.is_active = True
        self.user.save()
        self.profile: Profile = Profile.objects.create(user=self.user, age=20, signup_step=6)

    def test_profile_views_require_login(self) -> None:
        profile_url: str = reverse('accounts:profile')
        password_url: str = reverse('accounts:password_change')
        
        response1 = self.client.get(profile_url)
        self.assertRedirects(response1, f"{reverse('accounts:login')}?next={profile_url}")
        
        response2 = self.client.get(password_url)
        self.assertRedirects(response2, f"{reverse('accounts:login')}?next={password_url}")

    def test_profile_modification_success(self) -> None:
        self.client.login(username='testuser@pusan.ac.kr', password='OldPassword123')
        
        profile_url: str = reverse('accounts:profile')
        post_data: dict[str, str] = {
            'name': '김철수',
            'age': '25',
        }
        
        response = self.client.post(profile_url, post_data)
        self.assertRedirects(response, profile_url)
        
        self.user.refresh_from_db()
        self.profile.refresh_from_db()
        # They should NOT be changed
        self.assertEqual(self.user.first_name, '홍길동')
        self.assertEqual(self.profile.age, 20)

    def test_profile_modification_xss_protection(self) -> None:
        self.client.login(username='testuser@pusan.ac.kr', password='OldPassword123')
        
        profile_url: str = reverse('accounts:profile')
        post_data: dict[str, str] = {
            'name': '<script>alert("hacked")</script>',
            'age': '25',
        }
        
        response = self.client.post(profile_url, post_data)
        self.assertRedirects(response, profile_url)
        
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, '홍길동')

    def test_password_change_success(self) -> None:
        self.client.login(username='testuser@pusan.ac.kr', password='OldPassword123')
        
        password_url: str = reverse('accounts:password_change')
        post_data: dict[str, str] = {
            'current_password': 'OldPassword123',
            'new_password': 'PnuCreditCampusNew123!',
            'confirm_new_password': 'PnuCreditCampusNew123!'
        }
        
        response = self.client.post(password_url, post_data)
        self.assertRedirects(response, reverse('accounts:profile'))
        
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('PnuCreditCampusNew123!'))

    def test_password_change_incorrect_current_password(self) -> None:
        self.client.login(username='testuser@pusan.ac.kr', password='OldPassword123')
        
        password_url: str = reverse('accounts:password_change')
        post_data: dict[str, str] = {
            'current_password': 'WrongOldPassword',
            'new_password': 'PnuCreditCampusNew123!',
            'confirm_new_password': 'PnuCreditCampusNew123!'
        }
        
        response = self.client.post(password_url, post_data)
        self.assertEqual(response.status_code, 200)
        
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('OldPassword123'))

    def test_withdraw_success(self) -> None:
        self.client.login(username='testuser@pusan.ac.kr', password='OldPassword123')
        
        withdraw_url: str = reverse('accounts:withdraw')
        post_data: dict[str, str] = {
            'password': 'OldPassword123'
        }
        
        response = self.client.post(withdraw_url, post_data)
        self.assertRedirects(response, reverse('main:index'))
        
        with self.assertRaises(User.DoesNotExist):
            User.objects.get(username='testuser@pusan.ac.kr')

    def test_withdraw_incorrect_password(self) -> None:
        self.client.login(username='testuser@pusan.ac.kr', password='OldPassword123')
        
        withdraw_url: str = reverse('accounts:withdraw')
        post_data: dict[str, str] = {
            'password': 'IncorrectPassword'
        }
        
        response = self.client.post(withdraw_url, post_data)
        self.assertEqual(response.status_code, 200)
        
        user_exists: bool = User.objects.filter(username='testuser@pusan.ac.kr').exists()
        self.assertTrue(user_exists)

    def test_withdraw_brute_force_prevention(self) -> None:
        self.client.login(username='testuser@pusan.ac.kr', password='OldPassword123')
        withdraw_url: str = reverse('accounts:withdraw')
        
        for i in range(4):
            response = self.client.post(withdraw_url, {'password': 'WrongPassword'})
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, f"실패 횟수: {i+1}/5")
            
        response = self.client.post(withdraw_url, {'password': 'WrongPassword'})
        self.assertRedirects(response, reverse('accounts:login'))
        
        response_profile = self.client.get(reverse('accounts:profile'))
        self.assertEqual(response_profile.status_code, 302)


class PasswordResetTests(TestCase):
    def setUp(self) -> None:
        self.client: Client = Client()
        cache.clear()
        self.user: User = User.objects.create_user(
            username='resetuser@pusan.ac.kr',
            email='resetuser@pusan.ac.kr',
            password='OldPassword123!',
            first_name='길동'
        )
        self.user.is_active = True
        self.user.save()
        Profile.objects.create(user=self.user, signup_step=6)
        mail.outbox = []

    def test_find_password_invalid_email_domain(self) -> None:
        find_url: str = reverse('accounts:find_password')
        response = self.client.post(find_url, {'email': 'test@naver.com'})
        self.assertEqual(response.status_code, 200)
        msgs = list(get_messages(response.wsgi_request))
        self.assertTrue(any("부산대학교 이메일 주소만 사용 가능합니다" in m.message for m in msgs))

    def test_find_password_user_not_exist(self) -> None:
        find_url: str = reverse('accounts:find_password')
        response = self.client.post(find_url, {'email': 'noone@pusan.ac.kr'})
        
        # User enumeration mitigation: behaves identical to success (redirects)
        self.assertRedirects(response, reverse('accounts:find_password_verify_code'))
        self.assertEqual(self.client.session.get('pwd_reset_email'), 'noone@pusan.ac.kr')
        
        # But no email should actually be sent
        self.assertEqual(len(mail.outbox), 0)
        
        # Verify fake code was cached internally anyway to keep stages uniform
        code: str | None = cache.get('pwd_reset_code:noone@pusan.ac.kr')
        self.assertIsNotNone(code)

    def test_find_password_sends_email_and_redirects(self) -> None:
        find_url: str = reverse('accounts:find_password')
        response = self.client.post(find_url, {'email': 'resetuser@pusan.ac.kr'})
        
        self.assertRedirects(response, reverse('accounts:find_password_verify_code'))
        self.assertEqual(self.client.session.get('pwd_reset_email'), 'resetuser@pusan.ac.kr')
        self.assertEqual(len(mail.outbox), 1)
        
        # Verify cached code exists
        code: str | None = cache.get('pwd_reset_code:resetuser@pusan.ac.kr')
        self.assertIsNotNone(code)
        self.assertEqual(len(code), 6)

    def test_find_password_rate_limit(self) -> None:
        find_url: str = reverse('accounts:find_password')
        # First request
        self.client.post(find_url, {'email': 'resetuser@pusan.ac.kr'})
        self.assertEqual(len(mail.outbox), 1)
        
        # Second immediate request
        mail.outbox = []
        response = self.client.post(find_url, {'email': 'resetuser@pusan.ac.kr'})
        self.assertEqual(len(mail.outbox), 0)
        
        msgs = list(get_messages(response.wsgi_request))
        self.assertTrue(any("이미 비밀번호 재설정 이메일이 발송되었습니다" in m.message for m in msgs))

    def test_find_password_verify_code_success(self) -> None:
        # Request code
        self.client.post(reverse('accounts:find_password'), {'email': 'resetuser@pusan.ac.kr'})
        code: str = cache.get('pwd_reset_code:resetuser@pusan.ac.kr')
        
        verify_url: str = reverse('accounts:find_password_verify_code')
        response = self.client.post(verify_url, {'code': code})
        
        self.assertRedirects(response, reverse('accounts:find_password_reset'))
        
        # Session should contain token and verified email
        self.assertEqual(self.client.session.get('pwd_reset_verified_email'), 'resetuser@pusan.ac.kr')
        self.assertIsNotNone(self.client.session.get('pwd_reset_token'))
        self.assertIsNone(self.client.session.get('pwd_reset_email'))

    def test_find_password_verify_code_invalid(self) -> None:
        self.client.post(reverse('accounts:find_password'), {'email': 'resetuser@pusan.ac.kr'})
        
        verify_url: str = reverse('accounts:find_password_verify_code')
        response = self.client.post(verify_url, {'code': '000000'})  # Wrong code
        
        self.assertEqual(response.status_code, 200)
        msgs = list(get_messages(response.wsgi_request))
        self.assertTrue(any("올바르지 않은 인증 코드입니다" in m.message for m in msgs))
        
        attempts = cache.get('pwd_reset_attempts:resetuser@pusan.ac.kr')
        self.assertEqual(attempts, 1)

    def test_find_password_verify_code_lockout(self) -> None:
        self.client.post(reverse('accounts:find_password'), {'email': 'resetuser@pusan.ac.kr'})
        verify_url: str = reverse('accounts:find_password_verify_code')
        
        # Post wrong code 5 times
        for i in range(4):
            response = self.client.post(verify_url, {'code': '000000'})
            self.assertEqual(response.status_code, 200)
            
        # The 5th attempt locks out
        response = self.client.post(verify_url, {'code': '000000'})
        self.assertRedirects(response, reverse('accounts:find_password'))
        self.assertIsNone(self.client.session.get('pwd_reset_email'))
        
        # Verify code cache and attempts cache were cleared
        self.assertIsNone(cache.get('pwd_reset_code:resetuser@pusan.ac.kr'))

    def test_find_password_reset_success(self) -> None:
        # 1. Request email
        self.client.post(reverse('accounts:find_password'), {'email': 'resetuser@pusan.ac.kr'})
        code: str = cache.get('pwd_reset_code:resetuser@pusan.ac.kr')
        
        # 2. Verify code
        self.client.post(reverse('accounts:find_password_verify_code'), {'code': code})
        
        # 3. Reset password
        reset_url: str = reverse('accounts:find_password_reset')
        response = self.client.post(reset_url, {
            'new_password': 'PnuCreditCampusNew123!',
            'confirm_new_password': 'PnuCreditCampusNew123!'
        })
        
        # Should redirect to login page
        self.assertRedirects(response, reverse('accounts:login'))
        
        # The user password should be updated
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('PnuCreditCampusNew123!'))
        
        # The session should be flushed (no reset info left)
        self.assertIsNone(self.client.session.get('pwd_reset_token'))

    def test_find_password_reset_mismatch(self) -> None:
        # 1. Request email
        self.client.post(reverse('accounts:find_password'), {'email': 'resetuser@pusan.ac.kr'})
        code: str = cache.get('pwd_reset_code:resetuser@pusan.ac.kr')
        
        # 2. Verify code
        self.client.post(reverse('accounts:find_password_verify_code'), {'code': code})
        
        # 3. Try to reset with non-matching passwords
        reset_url: str = reverse('accounts:find_password_reset')
        response = self.client.post(reset_url, {
            'new_password': 'Password123!',
            'confirm_new_password': 'DifferentPassword123!'
        })
        self.assertEqual(response.status_code, 200)
        msgs = list(get_messages(response.wsgi_request))
        self.assertTrue(any("새 비밀번호가 일치하지 않습니다" in m.message for m in msgs))
