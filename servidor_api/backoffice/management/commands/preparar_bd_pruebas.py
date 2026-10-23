"""
Crea (o elimina) la base de datos de pruebas: una copia exacta de la real.

    python manage.py preparar_bd_pruebas            # copia OpticaModaVisual -> OpticaModaVisual_pruebas
    python manage.py preparar_bd_pruebas --eliminar # borra la copia

La copia conserva esquemas, triggers, vistas, secuencias y datos, así que las
pruebas de integración corren contra el mismo motor y las mismas reglas que
producción, sin tocar los datos reales. El respaldo es COPY_ONLY: no altera
la cadena de respaldos de la base real.
"""
import pyodbc
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

SUFIJO = "_pruebas"


def _conexion_master():
    bd = settings.DATABASES["default"]
    opciones = bd.get("OPTIONS", {})
    cadena = (
        f"DRIVER={{{opciones.get('driver', 'ODBC Driver 18 for SQL Server')}}};"
        f"SERVER={bd['HOST']};DATABASE=master;{opciones.get('extra_params', '')}"
    )
    return pyodbc.connect(cadena, autocommit=True)


class Command(BaseCommand):
    help = "Crea una copia de la base de datos para pruebas de integración (o la elimina)."

    def add_arguments(self, parser):
        parser.add_argument("--eliminar", action="store_true", help="Elimina la copia de pruebas.")

    def handle(self, *args, **opciones):
        original = settings.DATABASES["default"]["NAME"]
        if original.endswith(SUFIJO):
            raise CommandError("La configuración ya apunta a la base de pruebas.")
        copia = original + SUFIJO

        cursor = _conexion_master().cursor()
        cursor.execute(
            f"IF DB_ID(N'{copia}') IS NOT NULL BEGIN "
            f"ALTER DATABASE [{copia}] SET SINGLE_USER WITH ROLLBACK IMMEDIATE; "
            f"DROP DATABASE [{copia}]; END"
        )
        if opciones["eliminar"]:
            self.stdout.write(self.style.SUCCESS(f"Base de pruebas {copia} eliminada."))
            return

        respaldos, datos, logs = cursor.execute(
            "SELECT CAST(SERVERPROPERTY('InstanceDefaultBackupPath') AS nvarchar(400)), "
            "CAST(SERVERPROPERTY('InstanceDefaultDataPath') AS nvarchar(400)), "
            "CAST(SERVERPROPERTY('InstanceDefaultLogPath') AS nvarchar(400))"
        ).fetchone()
        archivo = respaldos.rstrip("\\") + f"\\{copia}.bak"

        self.stdout.write(f"Respaldando {original} (COPY_ONLY)...")
        cursor.execute(f"BACKUP DATABASE [{original}] TO DISK = N'{archivo}' WITH COPY_ONLY, INIT")
        while cursor.nextset():
            pass

        movimientos = []
        for f in cursor.execute(f"RESTORE FILELISTONLY FROM DISK = N'{archivo}'").fetchall():
            carpeta = (datos if f.Type == "D" else logs).rstrip("\\")
            extension = ".mdf" if f.Type == "D" else ".ldf"
            movimientos.append(f"MOVE N'{f.LogicalName}' TO N'{carpeta}\\{copia}_{f.LogicalName}{extension}'")

        self.stdout.write(f"Restaurando como {copia}...")
        cursor.execute(
            f"RESTORE DATABASE [{copia}] FROM DISK = N'{archivo}' WITH {', '.join(movimientos)}, RECOVERY"
        )
        while cursor.nextset():
            pass

        self.stdout.write(self.style.SUCCESS(f"Base de pruebas {copia} lista."))
