"""
Qué secciones del sistema puede usar cada rol.

El rol sale de seguridad.usuario (mismo username que la cuenta de login).
Los superusuarios de Django y los roles no listados en SECCIONES_POR_ROL
tienen acceso a todo.
"""
from negocio.servicios import usuarios

TODAS = frozenset({
    "inicio", "clientes", "citas", "clinica", "ventas", "facturas",
    "inventario", "reportes",
})

# Solo se listan los roles con acceso restringido.
SECCIONES_POR_ROL = {
    "OPTOMETRISTA": frozenset({"inicio", "clientes", "citas", "clinica"}),
}


def secciones_permitidas(user):
    if not user.is_authenticated:
        return frozenset()
    if user.is_superuser:
        return TODAS

    rol = (usuarios.rol_de_cuenta(user) or "").upper()
    return SECCIONES_POR_ROL.get(rol, TODAS)


def puede(user, seccion):
    """`seccion` vacía (login, páginas comunes) siempre está permitida."""
    return not seccion or seccion in secciones_permitidas(user)
