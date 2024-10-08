from django.apps import AppConfig


class DecidablesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'flowback.decidables'

    def ready(self) -> None:
        from . import logic
