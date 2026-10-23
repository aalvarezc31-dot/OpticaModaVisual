"""
Crea los usuarios de prueba (uno por rol) en la BASE DE PRUEBAS.

    set OPTICA_DB_NAME=OpticaModaVisual_pruebas
    python manage.py crear_usuarios_prueba

Se niega a ejecutarse contra la base real.
"""
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.db import connection

from datos.models import Rol, Usuario
from negocio.servicios import usuarios

CLAVE = "Prueba#2026"
USUARIOS = [
    ("prueba_admin", "ADMINISTRADOR", True),
    ("prueba_vende", "VENDEDOR", False),
    ("prueba_opto", "OPTOMETRISTA", False),
]


class Command(BaseCommand):
    help = "Crea usuarios de prueba (contraseña Prueba#2026) en la base de pruebas."

    def handle(self, *args, **opciones):
        if not connection.settings_dict["NAME"].endswith("_pruebas"):
            raise CommandError("Solo se ejecuta contra la base de pruebas (OPTICA_DB_NAME=..._pruebas).")

        for username, rol, superusuario in USUARIOS:
            cuenta = User.objects.filter(username=username).first() or User(
                username=username, first_name="Prueba", last_name=rol.title()
            )
            cuenta.set_password(CLAVE)
            cuenta.is_superuser = cuenta.is_staff = superusuario
            cuenta.save()

            usuario, _ = usuarios.enlazar_cuenta(cuenta)
            Usuario.objects.filter(pk=usuario.pk).update(id_rol=Rol.objects.get(nombre=rol).id_rol)
            self.stdout.write(f"{username} ({rol})")

        self.stdout.write(self.style.SUCCESS(f"Usuarios de prueba listos. Contraseña: {CLAVE}"))
