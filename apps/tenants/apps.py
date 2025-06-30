from django.apps import AppConfig


class TenantsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.tenants'
    
    def ready(self):
        # Import signals to ensure they are connected
        from . import signals
