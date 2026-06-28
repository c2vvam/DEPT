from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import AbstractBaseUser

class AllowInactiveUserModelBackend(ModelBackend):
    """
    Custom authentication backend that allows inactive users to authenticate.
    This prevents duplicate password hashing (timing attacks) in views,
    as we can verify both password and active status with a single authenticate() call.
    """
    def user_can_authenticate(self, user: AbstractBaseUser) -> bool:
        # Allow inactive users to authenticate
        return True
