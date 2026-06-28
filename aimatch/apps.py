import os
from django.apps import AppConfig
from django.conf import settings


class AimatchConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'aimatch'

    def ready(self) -> None:
        if os.environ.get('RUN_MAIN') == 'true' or not settings.DEBUG:
            from .services.match_service import start_timer_thread
            start_timer_thread()

