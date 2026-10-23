"""Datos disponibles en todas las plantillas."""
from negocio.servicios import permisos

# Primer segmento de la URL -> sección del sistema.
SECCIONES = {
    "": "inicio",
    "clientes": "clientes",
    "citas": "citas",
    "examenes": "clinica",
    "resultados": "clinica",
    "recetas": "clinica",
    "ventas": "ventas",
    "facturas": "facturas",
    "productos": "inventario",
    "proveedores": "inventario",
    "catalogos": "inventario",
    "reportes": "reportes",
}


def seccion_de_ruta(path):
    segmentos = path.strip("/").split("/")

    # Cobrar una cita crea una venta: pertenece a Ventas.
    if segmentos[0] == "citas" and segmentos[-1] == "cobrar":
        return "ventas"

    return SECCIONES.get(segmentos[0], "")


def secciones_del_usuario(request):
    """Secciones permitidas, calculadas una sola vez por petición."""
    if not hasattr(request, "_secciones_permitidas"):
        request._secciones_permitidas = permisos.secciones_permitidas(request.user)
    return request._secciones_permitidas


def seccion_actual(request):
    return {
        "seccion": seccion_de_ruta(request.path),
        "permisos": secciones_del_usuario(request) if hasattr(request, "user") else frozenset(),
    }
