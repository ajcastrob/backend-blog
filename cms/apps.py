from django.apps import AppConfig


class CmsConfig(AppConfig):
    name = "cms"

    def ready(self):
        from . import signals  # noqa: F401
