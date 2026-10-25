"""
Enlace entre las cuentas de login de Django (auth_user) y los usuarios
del sistema con rol (seguridad.usuario). Se enlazan por el mismo username.
"""
from django.contrib.auth.hashers import make_password
from django.utils import timezone

from datos.repositorios import usuarios as repo_usuarios

ROL_ADMINISTRADOR = "ADMINISTRADOR"
ROL_POR_DEFECTO = "VENDEDOR"  # en pantalla se muestra como "Agente"


def rol_de_cuenta(user):
    """Nombre del rol del usuario del sistema enlazado a la cuenta, o None."""
    usuario = repo_usuarios.buscar_por_username(user.get_username())
    if usuario is None:
        return None
    rol = repo_usuarios.mapa_roles().get(usuario.id_rol)
    return rol.nombre if rol else None


def _email_libre(user, excluir_id=None):
    email = (user.email or "").strip()
    if email and not repo_usuarios.email_en_uso(email, excluir_id):
        return email
    # email es único en seguridad.usuario: se genera uno interno si falta.
    return f"{user.get_username().lower()}@opticamodavisual.local"


def enlazar_cuenta(user):
    """
    Crea el usuario del sistema de una cuenta de login, o actualiza sus datos.

    Si es nuevo recibe el rol ADMINISTRADOR (superusuarios) o AGENTE; el rol
    se cambia después desde el panel. Devuelve (usuario, creado).
    """
    existente = repo_usuarios.buscar_por_username(user.get_username())

    datos = {
        "nombres": (user.first_name or user.get_username())[:80],
        "apellidos": (user.last_name or "")[:80],
        "activo": user.is_active,
    }

    if existente:
        datos["email"] = _email_libre(user, existente.id_usuario) if user.email else existente.email
        repo_usuarios.actualizar(existente.id_usuario, **datos)
        return existente, False

    rol = repo_usuarios.rol_por_nombre(
        ROL_ADMINISTRADOR if user.is_superuser else ROL_POR_DEFECTO
    ) or repo_usuarios.listar_roles().first()

    usuario = repo_usuarios.crear(
        **datos,
        id_rol=rol.id_rol,
        username=user.get_username()[:40],
        email=_email_libre(user),
        password_hash=make_password(None),  # inicia sesión con su cuenta de Django
        telefono=None,
        ultimo_acceso=None,
        fecha_creacion=timezone.now(),
    )
    return usuario, True
