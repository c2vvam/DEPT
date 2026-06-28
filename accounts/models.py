from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    age = models.PositiveIntegerField(null=True, blank=True)
    
    # New fields for multi-step signup
    admission_year = models.PositiveIntegerField(null=True, blank=True)
    department = models.CharField(max_length=100, default='자유전공학부')
    signup_step = models.PositiveSmallIntegerField(default=1)
    
    nickname = models.CharField(max_length=100, blank=True, null=True)
    profile_image_url = models.URLField(max_length=500, blank=True, null=True)
    
    def __str__(self) -> str:
        return f"{self.user.username}"


