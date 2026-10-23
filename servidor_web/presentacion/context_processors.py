"""Datos disponibles en todas las plantillas."""
from django.conf import settings

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


def seccion_actual(request):
    usuario = getattr(request, "user", None)
    return {
        "seccion": seccion_de_ruta(request.path),
        "permisos": usuario.secciones if usuario is not None and usuario.is_authenticated else frozenset(),
        "url_admin": settings.URL_API.rstrip("/") + "/admin/",
    }
