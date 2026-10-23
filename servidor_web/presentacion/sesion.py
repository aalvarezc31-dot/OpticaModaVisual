"""
Sesión del servidor web sin base de datos.

Al iniciar sesión la API devuelve un token firmado, el rol y las secciones
permitidas; se guardan en la cookie de sesión (firmada) y en cada petición
se reconstruye `request.user` a partir de ella.
"""
from functools import wraps

from django.conf import settings
from django.shortcuts import redirect
from django.utils.http import urlencode

CLAVE = "usuario_api"


class UsuarioWeb:
    """Usuario de la petición (compatible con lo que usan las plantillas)."""

    def __init__(self, datos=None):
        datos = datos or {}
        self.token = datos.get("token")
        usuario = datos.get("usuario") or {}
        self.username = usuario.get("username", "")
        self.nombre = usuario.get("nombre", "")
        self.is_staff = bool(usuario.get("is_staff"))
        self.is_superuser = bool(usuario.get("is_superuser"))
        self.rol = datos.get("rol")
        self.secciones = frozenset(datos.get("secciones") or [])

    @property
    def is_authenticated(self):
        return bool(self.token)

    def get_username(self):
        return self.username


def guardar(request, datos):
    request.session.cycle_key()
    request.session[CLAVE] = {
        "token": datos["token"],
        "usuario": dict(datos["usuario"]),
        "rol": datos.get("rol"),
        "secciones": list(datos.get("secciones") or []),
    }


def cerrar(request):
    request.session.flush()


def usuario_de(request):
    return UsuarioWeb(request.session.get(CLAVE))


def login_required(vista):
    """Redirige al login si no hay sesión (reemplaza al de django.contrib.auth)."""
    @wraps(vista)
    def envoltura(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f"{settings.LOGIN_URL}?{urlencode({'next': request.get_full_path()})}")
        return vista(request, *args, **kwargs)
    return envoltura
