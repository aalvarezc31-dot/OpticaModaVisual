"""
Módulo analítico: indicadores del dashboard y reportes exportables.

Los datos salen de las vistas del esquema [reportes] y de consultas de
datos/repositorios/reportes.py.
"""
from datetime import timedelta

from django.utils import timezone

from datos.repositorios import reportes as repo_reportes

PERIODOS = (7, 30, 90, 365)


def normalizar_dias(dias):
    try:
        dias = int(dias)
    except (TypeError, ValueError):
        return 30
    return dias if dias in PERIODOS else 30


def desde(dias):
    """Primer día del periodo de `dias` días que termina hoy."""
    return timezone.now().date() - timedelta(days=dias - 1)


def resumen(dias=30):
    inicio = desde(dias)
    diarias = repo_reportes.ventas_diarias(inicio)
    saldos = repo_reportes.saldos_pendientes()
    inventario = repo_reportes.inventario_valorizado()
    total_periodo = sum((d["total_vendido"] or 0) for d in diarias)
    ventas_periodo = sum((d["cantidad_ventas"] or 0) for d in diarias)
    citas_estado = repo_reportes.citas_por_estado(inicio)

    return {
        "dias": dias,
        "periodos": PERIODOS,
        "ventas_diarias": diarias,
        "total_periodo": total_periodo,
        "ventas_periodo": ventas_periodo,
        "ticket_promedio": (total_periodo / ventas_periodo) if ventas_periodo else 0,
        "por_vendedor": repo_reportes.ventas_por_vendedor(),
        "mas_vendidos": repo_reportes.productos_mas_vendidos(),
        "por_categoria": repo_reportes.ventas_por_categoria(inicio),
        "citas_estado": citas_estado,
        "total_citas": sum(c["cantidad"] for c in citas_estado),
        "citas_atendidas": sum(c["cantidad"] for c in citas_estado if c["estado"] == "ATENDIDA"),
        "stock_bajo": repo_reportes.stock_bajo(),
        "saldos": saldos,
        "saldo_total": sum((s["saldo"] or 0) for s in saldos),
        "valor_inventario": sum((p["valor_costo"] or 0) for p in inventario),
        "reportes_exportables": [(nombre, r[0]) for nombre, r in REPORTES.items()],
    }


def tablero(dias=30):
    """Indicadores + series de las gráficas del dashboard."""
    contexto = resumen(normalizar_dias(dias))
    contexto["graficas"] = datos_graficas(contexto)
    return contexto


def datos_graficas(contexto):
    """Series listas para las gráficas del dashboard (números simples, sin Decimal)."""
    diarias = sorted(contexto["ventas_diarias"], key=lambda d: d["fecha"])
    return {
        "diarias": {
            "etiquetas": [d["fecha"].strftime("%d/%m") for d in diarias],
            "totales": [float(d["total_vendido"] or 0) for d in diarias],
            "cantidades": [int(d["cantidad_ventas"] or 0) for d in diarias],
        },
        "categorias": {
            "etiquetas": [c["categoria"] for c in contexto["por_categoria"]],
            "montos": [float(c["monto"] or 0) for c in contexto["por_categoria"]],
        },
        "vendedores": {
            "etiquetas": [v["vendedor_nombre"] for v in contexto["por_vendedor"]],
            "montos": [float(v["total_vendido"] or 0) for v in contexto["por_vendedor"]],
        },
        "productos": {
            "etiquetas": [p["codigo"] + " · " + p["nombre"] for p in contexto["mas_vendidos"]],
            "unidades": [int(p["unidades_vendidas"] or 0) for p in contexto["mas_vendidos"]],
        },
        "citas": {
            "etiquetas": [c["estado"] for c in contexto["citas_estado"]],
            "cantidades": [int(c["cantidad"]) for c in contexto["citas_estado"]],
        },
    }


# --- Reportes exportables ---
# nombre -> (título, [(columna, encabezado)], función(dias) -> filas)
REPORTES = {
    "ventas-diarias": (
        "Ventas diarias",
        [("fecha", "Fecha"), ("cantidad_ventas", "Ventas"), ("subtotal", "Subtotal (Q)"),
         ("descuentos", "Descuentos (Q)"), ("total_vendido", "Total (Q)")],
        lambda dias: repo_reportes.ventas_diarias(desde(dias)),
    ),
    "ventas-por-vendedor": (
        "Ventas por vendedor",
        [("vendedor_nombre", "Vendedor"), ("cantidad_ventas", "Ventas"), ("total_vendido", "Total (Q)")],
        lambda dias: repo_reportes.ventas_por_vendedor(),
    ),
    "ventas-por-categoria": (
        "Ventas por categoría",
        [("categoria", "Categoría"), ("unidades", "Unidades"), ("monto", "Monto (Q)")],
        lambda dias: repo_reportes.ventas_por_categoria(desde(dias)),
    ),
    "productos-mas-vendidos": (
        "Productos más vendidos",
        [("codigo", "Código"), ("nombre", "Producto"), ("unidades_vendidas", "Unidades"),
         ("ingresos", "Ingresos (Q)")],
        lambda dias: repo_reportes.productos_mas_vendidos(limite=50),
    ),
    "inventario": (
        "Inventario valorizado",
        [("codigo", "Código"), ("nombre", "Producto"), ("categoria", "Categoría"), ("marca", "Marca"),
         ("stock_actual", "Existencias"), ("stock_minimo", "Mínimo"), ("precio_costo", "Costo (Q)"),
         ("precio_venta", "Precio (Q)"), ("valor_costo", "Valor al costo (Q)"),
         ("valor_venta", "Valor a precio de venta (Q)")],
        lambda dias: repo_reportes.inventario_valorizado(),
    ),
    "stock-bajo": (
        "Productos con stock bajo",
        [("codigo", "Código"), ("nombre", "Producto"), ("categoria", "Categoría"),
         ("proveedor", "Proveedor"), ("telefono_proveedor", "Teléfono proveedor"),
         ("stock_actual", "Existencias"), ("stock_minimo", "Mínimo")],
        lambda dias: repo_reportes.stock_bajo(),
    ),
    "saldos-por-cobrar": (
        "Saldos por cobrar",
        [("id_venta", "Venta"), ("fecha_venta", "Fecha"), ("cliente_nombre", "Cliente"),
         ("total", "Total (Q)"), ("pagado", "Pagado (Q)"), ("saldo", "Saldo (Q)"), ("estado", "Estado")],
        lambda dias: repo_reportes.saldos_pendientes(),
    ),
    "citas": (
        "Agenda de citas",
        [("fecha_hora_inicio", "Fecha y hora"), ("tipo_cita", "Tipo"), ("cliente_nombre", "Paciente"),
         ("cliente_telefono", "Teléfono"), ("usuario_atiende_nombre", "Optometrista"), ("estado", "Estado")],
        lambda dias: repo_reportes.citas_del_periodo(desde(dias)),
    ),
}


def exportacion(nombre, dias):
    """Devuelve (título, encabezados, filas como listas) o None si el reporte no existe."""
    if nombre not in REPORTES:
        return None

    titulo, columnas, consulta = REPORTES[nombre]
    filas = [[fila.get(columna) for columna, _ in columnas] for fila in consulta(dias)]
    return titulo, [encabezado for _, encabezado in columnas], filas
