from django.apps import AppConfig


class DatosConfig(AppConfig):
    """Capa de datos: modelos ORM y repositorios de acceso a la BD."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'datos'
    verbose_name = 'Capa de datos'
