"""Datos disponibles en todas las plantillas."""

# Primer segmento de la URL -> sección del menú que se marca como activa.
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


def seccion_actual(request):
    primer_segmento = request.path.strip("/").split("/")[0]
    return {"seccion": SECCIONES.get(primer_segmento, "")}
