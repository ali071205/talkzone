from django.apps import AppConfig


class ARtchatConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'a_rtchat'

    def ready(self):
        try:
            from .models import ChatGroup
            for group in ChatGroup.objects.all():
                group.users_online.clear()
        except Exception:
            pass