from django.apps import AppConfig


class BackofficeConfig(AppConfig):
    """Panel administrativo de Django (/admin/) y comandos de mantenimiento."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backoffice'
    verbose_name = 'Administración'
