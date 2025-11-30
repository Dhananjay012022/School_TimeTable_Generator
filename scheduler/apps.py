from django.apps import AppConfig


class SchedulerConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "scheduler"

    def ready(self):
        # Import signals so that UserProfile gets created/updated automatically
        from . import signals  # noqa
