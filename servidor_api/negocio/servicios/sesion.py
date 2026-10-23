from django.conf import settings

from datos.models import Usuario
from datos.repositorios import usuarios as repo_usuarios
from negocio.excepciones import ReglaNegocioError


def usuario_actual(user):
    """
    Devuelve el registro de seguridad.usuario del usuario que inició sesión.

    El login usa las cuentas de Django (auth_user); se enlazan con
    seguridad.usuario por el mismo `username`. Si no hay coincidencia se usa
    settings.ID_USUARIO_SISTEMA_PREDETERMINADO (None = exigir coincidencia).
    """
    usuario = repo_usuarios.obtener_por_username(user.get_username())
    id_predeterminado = getattr(settings, "ID_USUARIO_SISTEMA_PREDETERMINADO", None)

    if usuario is None and id_predeterminado:
        try:
            usuario = repo_usuarios.obtener_activo(id_predeterminado)
        except Usuario.DoesNotExist:
            usuario = None

    if usuario is None:
        raise ReglaNegocioError(
            f"Tu usuario '{user.get_username()}' no existe (o está inactivo) "
            "en seguridad.usuario. Pide que lo registren con el mismo nombre de usuario."
        )

    return usuario


def nombre_completo(usuario):
    return f"{usuario.nombres} {usuario.apellidos}"
