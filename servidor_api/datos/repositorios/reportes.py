"""
Consultas de reportes: vistas del esquema [reportes] y consultas sobre ventas,
inventario y citas. Los reportes de un periodo reciben `desde` y `hasta`
(fechas, ambos inclusive).
"""
from django.db import connection

# Ventas que cuentan como vendidas (confirmadas en adelante).
VENTA_VALIDA = "v.estado NOT IN (N'PENDIENTE', N'ANULADA')"


def _consultar(sql, parametros=()):
    with connection.cursor() as cursor:
        cursor.execute(sql, parametros)
        columnas = [c[0] for c in cursor.description]
        return [dict(zip(columnas, fila)) for fila in cursor.fetchall()]


def ventas_diarias(desde, hasta):
    return _consultar(
        "SELECT fecha, cantidad_ventas, subtotal, descuentos, total_vendido "
        "FROM reportes.vw_ventas_diarias WHERE fecha BETWEEN %s AND %s ORDER BY fecha DESC",
        [desde, hasta],
    )


def ventas_por_agente(desde, hasta):
    """Ventas por agente (columna vendedor_* de la BD) en el periodo."""
    return _consultar(
        "SELECT v.vendedor_nombre AS agente_nombre, COUNT(*) AS cantidad_ventas, "
        "SUM(v.total) AS total_vendido FROM ventas.venta v "
        f"WHERE {VENTA_VALIDA} AND CAST(v.fecha_venta AS date) BETWEEN %s AND %s "
        "GROUP BY v.vendedor_nombre ORDER BY total_vendido DESC",
        [desde, hasta],
    )


def productos_mas_vendidos(desde, hasta, limite=10):
    """Productos (no servicios) con más unidades vendidas en el periodo."""
    return _consultar(
        "SELECT TOP (%s) p.codigo, p.nombre, SUM(dv.cantidad) AS unidades_vendidas, "
        "SUM(dv.subtotal) AS ingresos "
        "FROM ventas.detalle_venta dv "
        "JOIN ventas.venta v ON v.id_venta = dv.id_venta "
        "JOIN inventario.producto p ON p.id_producto = dv.id_producto "
        f"WHERE {VENTA_VALIDA} AND dv.es_servicio = 0 "
        "AND CAST(v.fecha_venta AS date) BETWEEN %s AND %s "
        "GROUP BY p.codigo, p.nombre ORDER BY unidades_vendidas DESC",
        [limite, desde, hasta],
    )


def ventas_por_categoria(desde, hasta):
    """Monto vendido por categoría de producto en el periodo."""
    return _consultar(
        "SELECT c.nombre AS categoria, SUM(dv.cantidad) AS unidades, SUM(dv.subtotal) AS monto "
        "FROM ventas.detalle_venta dv "
        "JOIN ventas.venta v ON v.id_venta = dv.id_venta "
        "JOIN inventario.producto p ON p.id_producto = dv.id_producto "
        "JOIN inventario.categoria_producto c ON c.id_categoria = p.id_categoria "
        f"WHERE {VENTA_VALIDA} AND CAST(v.fecha_venta AS date) BETWEEN %s AND %s "
        "GROUP BY c.nombre ORDER BY monto DESC",
        [desde, hasta],
    )


def citas_por_estado(desde, hasta):
    return _consultar(
        "SELECT UPPER(estado) AS estado, COUNT(*) AS cantidad FROM citas.cita "
        "WHERE CAST(fecha_hora_inicio AS date) BETWEEN %s AND %s "
        "GROUP BY UPPER(estado) ORDER BY cantidad DESC",
        [desde, hasta],
    )


def citas_del_periodo(desde, hasta):
    return _consultar(
        "SELECT fecha_hora_inicio, tipo_cita, cliente_nombre, cliente_telefono, "
        "usuario_atiende_nombre, estado FROM reportes.vw_agenda_citas "
        "WHERE CAST(fecha_hora_inicio AS date) BETWEEN %s AND %s ORDER BY fecha_hora_inicio",
        [desde, hasta],
    )


# --- Reportes al día (no dependen del periodo) ---

def stock_bajo():
    return _consultar(
        "SELECT id_producto, codigo, nombre, categoria, proveedor, telefono_proveedor, "
        "stock_actual, stock_minimo FROM reportes.vw_stock_bajo ORDER BY stock_actual"
    )


def saldos_pendientes():
    return _consultar(
        "SELECT id_venta, fecha_venta, cliente_nombre, total, pagado, saldo, estado "
        "FROM reportes.vw_saldo_ventas ORDER BY fecha_venta"
    )


def historial_cliente(id_cliente):
    filas = _consultar(
        "SELECT total_examenes, ultimo_examen, citas_atendidas, citas_no_asistidas, "
        "total_compras, monto_comprado, ultima_compra "
        "FROM reportes.vw_historial_cliente WHERE id_cliente = %s",
        [id_cliente],
    )
    return filas[0] if filas else None


def inventario_valorizado():
    """Existencias y valor (costo y venta) de cada producto activo que maneja stock."""
    return _consultar(
        "SELECT p.codigo, p.nombre, c.nombre AS categoria, ISNULL(m.nombre, N'') AS marca, "
        "p.stock_actual, p.stock_minimo, p.precio_costo, p.precio_venta, "
        "p.stock_actual * p.precio_costo AS valor_costo, p.stock_actual * p.precio_venta AS valor_venta "
        "FROM inventario.producto p "
        "JOIN inventario.categoria_producto c ON c.id_categoria = p.id_categoria "
        "LEFT JOIN inventario.marca m ON m.id_marca = p.id_marca "
        "WHERE p.activo = 1 AND p.es_servicio = 0 ORDER BY c.nombre, p.nombre"
    )
