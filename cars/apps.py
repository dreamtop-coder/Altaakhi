from django.apps import AppConfig


class CarsConfig(AppConfig):
    name = "cars"
    def ready(self):
        # Import maintenance models here to ensure they are registered
        # after the app registry is ready, avoiding AppRegistryNotReady errors.
        try:
            from . import maintenance_models  # noqa: F401
        except Exception:
            # Avoid raising during management commands that may import apps early
            pass
