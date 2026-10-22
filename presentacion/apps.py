from django.apps import AppConfig


class PresentacionConfig(AppConfig):
    """Capa de presentación: vistas, formularios, URLs y plantillas."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'presentacion'
    verbose_name = 'Capa de presentación'
