"""
Catálogo de operaciones que la API expone: POST /api/v1/<módulo>/<operación>/

Solo lo que está aquí se puede llamar desde el servidor web. Cada módulo
indica la sección (permiso por rol, ver negocio/servicios/permisos.py) que
exige, y cada operación si necesita el usuario que hace la petición.
"""
from negocio.servicios import (
    catalogos, citas, clientes, examenes, facturas, panel, productos, recetas,
    reportes, ventas,
)

CON_USUARIO = True  # el servicio recibe el usuario autenticado como primer argumento

# módulo -> (servicio, sección que exige, {operación: necesita_usuario})
OPERACIONES = {
    "panel": (panel, "inicio", {
        "resumen_inicio": False,
    }),
    "clientes": (clientes, "clientes", {
        "buscar": False, "pacientes_activos": False, "obtener": False, "registrar": False,
        "actualizar": False, "cambiar_activo": False, "ficha": False,
    }),
    "citas": (citas, "citas", {
        "buscar_con_acciones": False, "estados": False, "obtener": False,
        "opciones_formulario": False, "citas_para_examen": False,
        "registrar": CON_USUARIO, "cambiar_estado": False,
    }),
    "examenes": (examenes, "clinica", {
        "buscar_con_paciente": False, "optometristas_activos": False, "obtener": False,
        "ficha": False, "registrar": False,
    }),
    "recetas": (recetas, "clinica", {
        "resultados": False, "examen_para_receta": False, "registrar": False, "ficha": False,
    }),
    "productos": (productos, "inventario", {
        "buscar": False, "obtener": False, "opciones_catalogo": False, "tipos_movimiento": False,
        "registrar": CON_USUARIO, "actualizar": False, "cambiar_activo": False, "ficha": False,
        "registrar_movimiento": CON_USUARIO,
    }),
    "catalogos": (catalogos, "inventario", {
        "categorias": False, "obtener_categoria": False, "guardar_categoria": False,
        "marcas": False, "obtener_marca": False, "guardar_marca": False,
        "proveedores": False, "obtener_proveedor": False, "guardar_proveedor": False,
        "cambiar_activo_proveedor": False,
    }),
    "ventas": (ventas, "ventas", {
        "estados": False, "buscar": False, "obtener": False, "opciones_nueva_venta": False,
        "crear": CON_USUARIO, "ficha": False, "agregar_producto": False, "quitar_linea": False,
        "aplicar_descuento": False, "confirmar": CON_USUARIO, "registrar_pago": CON_USUARIO,
        "entregar": False, "anular": CON_USUARIO, "metodos_de_pago": False,
        "cobrar_cita": CON_USUARIO, "productos_para_venta": False,
    }),
    "facturas": (facturas, "facturas", {
        "estados": False, "buscar": False, "obtener": False, "ficha": False,
        "datos_receptor": False, "emitir": CON_USUARIO, "anular": False,
    }),
    "reportes": (reportes, "reportes", {
        "tablero": False, "exportacion": False,
    }),
}


def buscar(modulo, operacion):
    """Devuelve (función, sección, necesita_usuario) o None si no está publicada."""
    if modulo not in OPERACIONES:
        return None

    servicio, seccion, publicadas = OPERACIONES[modulo]
    if operacion not in publicadas:
        return None

    return getattr(servicio, operacion), seccion, publicadas[operacion]
