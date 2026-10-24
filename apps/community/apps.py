from django.apps import AppConfig


class CommunityConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.community"
    verbose_name = "Community Desk"

    def ready(self):
        from . import signals  # noqa: F401
