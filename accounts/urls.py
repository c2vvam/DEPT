from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('terms/', views.terms_view, name='terms'),
    path('privacy/', views.privacy_view, name='privacy'),
    path('signup-extra/', views.signup_extra_view, name='signup_extra'),
    path('signup-id-card/', views.signup_id_card_view, name='signup_id_card'),
    path('logout/', views.logout_view, name='logout'),
    path('verification-needed/', views.verification_needed_view, name='verification_needed'),
    path('verify/<str:uidb64>/<str:token>/', views.verify_email_view, name='verify_email'),
    path('profile/', views.profile_view, name='profile'),
    path('password-change/', views.password_change_view, name='password_change'),
    path('withdraw/', views.withdraw_view, name='withdraw'),
    path('find-password/', views.find_password_view, name='find_password'),
    path('find-password/verify/', views.find_password_verify_code_view, name='find_password_verify_code'),
    path('find-password/reset/', views.find_password_reset_view, name='find_password_reset'),
]
