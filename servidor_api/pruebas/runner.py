"""
Ejecutor de pruebas del servidor API.

- Las pruebas que usan base de datos corren SIEMPRE sobre la copia
  <BD>_pruebas (DATABASES.default.TEST.NAME), nunca sobre la base real.
- No crea ni destruye esa copia (keepdb): se prepara con
  `python manage.py preparar_bd_pruebas`. Si no existe, se detiene con un aviso.
- Cada prueba de integración corre dentro de una transacción que se revierte.
"""
import pyodbc
from django.conf import settings
from django.test.runner import DiscoverRunner


def _existe_bd(nombre):
    bd = settings.DATABASES["default"]
    opciones = bd.get("OPTIONS", {})
    cadena = (f"DRIVER={{{opciones.get('driver', 'ODBC Driver 18 for SQL Server')}}};"
              f"SERVER={bd['HOST']};DATABASE=master;{opciones.get('extra_params', '')}")
    with pyodbc.connect(cadena, timeout=5) as conexion:
        return conexion.execute("SELECT DB_ID(?)", nombre).fetchone()[0] is not None


class Runner(DiscoverRunner):
    def __init__(self, *args, **kwargs):
        kwargs["keepdb"] = True  # nunca borrar ni recrear la base de pruebas
        super().__init__(*args, **kwargs)

    def setup_databases(self, **kwargs):
        if kwargs.get("aliases"):
            nombre = settings.DATABASES["default"]["TEST"]["NAME"]
            if not _existe_bd(nombre):
                raise SystemExit(
                    f"\nNo existe la base de pruebas {nombre}.\n"
                    "Créala con:  python manage.py preparar_bd_pruebas\n"
                    "(las pruebas unitarias se pueden correr sin ella: python manage.py test pruebas.unitarias)"
                )
        return super().setup_databases(**kwargs)
