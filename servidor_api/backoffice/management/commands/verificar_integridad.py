"""
Revisa la integridad de los datos entre esquemas (solo lectura).

    python manage.py verificar_integridad

Termina con código 1 si alguna verificación encuentra registros inconsistentes.
"""
from django.core.management.base import BaseCommand, CommandError

from datos.repositorios import integridad


class Command(BaseCommand):
    help = "Verifica la integridad de los datos entre esquemas (no modifica nada)."

    def handle(self, *args, **opciones):
        fallas = 0
        for codigo, descripcion, filas in integridad.ejecutar():
            if filas:
                fallas += 1
                self.stdout.write(self.style.ERROR(f"FALLA  {descripcion} ({len(filas)} registro(s))"))
                for fila in filas[:10]:
                    self.stdout.write(f"         {tuple(fila)}")
            else:
                self.stdout.write(self.style.SUCCESS(f"OK     {descripcion}"))

        total = len(integridad.VERIFICACIONES)
        if fallas:
            raise CommandError(f"{fallas} de {total} verificaciones encontraron inconsistencias.")
        self.stdout.write(self.style.SUCCESS(f"\nIntegridad correcta: {total} de {total} verificaciones."))
