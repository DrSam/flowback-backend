from django.apps import AppConfig


class GroupConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'flowback.group'

    def ready(self) -> None:
        from . import rules
