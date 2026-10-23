"""Consultas a las vistas del esquema [reportes] de la base de datos."""
from django.db import connection


def _consultar(sql, parametros=()):
    with connection.cursor() as cursor:
        cursor.execute(sql, parametros)
        columnas = [c[0] for c in cursor.description]
        return [dict(zip(columnas, fila)) for fila in cursor.fetchall()]


def ventas_diarias(desde):
    return _consultar(
        "SELECT fecha, cantidad_ventas, subtotal, descuentos, total_vendido "
        "FROM reportes.vw_ventas_diarias WHERE fecha >= %s ORDER BY fecha DESC",
        [desde],
    )


def ventas_por_vendedor():
    return _consultar(
        "SELECT vendedor_nombre, cantidad_ventas, total_vendido "
        "FROM reportes.vw_ventas_por_vendedor ORDER BY total_vendido DESC"
    )


def productos_mas_vendidos(limite=10):
    return _consultar(
        "SELECT TOP (%s) codigo, nombre, unidades_vendidas, ingresos "
        "FROM reportes.vw_productos_mas_vendidos ORDER BY unidades_vendidas DESC",
        [limite],
    )


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


def ventas_por_categoria(desde):
    """Monto vendido por categoría de producto (ventas confirmadas en adelante)."""
    return _consultar(
        "SELECT c.nombre AS categoria, SUM(dv.cantidad) AS unidades, SUM(dv.subtotal) AS monto "
        "FROM ventas.detalle_venta dv "
        "JOIN ventas.venta v ON v.id_venta = dv.id_venta "
        "JOIN inventario.producto p ON p.id_producto = dv.id_producto "
        "JOIN inventario.categoria_producto c ON c.id_categoria = p.id_categoria "
        "WHERE v.estado NOT IN (N'PENDIENTE', N'ANULADA') AND CAST(v.fecha_venta AS date) >= %s "
        "GROUP BY c.nombre ORDER BY monto DESC",
        [desde],
    )


def citas_por_estado(desde):
    return _consultar(
        "SELECT UPPER(estado) AS estado, COUNT(*) AS cantidad FROM citas.cita "
        "WHERE CAST(fecha_hora_inicio AS date) >= %s GROUP BY UPPER(estado) ORDER BY cantidad DESC",
        [desde],
    )


def citas_del_periodo(desde):
    return _consultar(
        "SELECT fecha_hora_inicio, tipo_cita, cliente_nombre, cliente_telefono, "
        "usuario_atiende_nombre, estado FROM reportes.vw_agenda_citas "
        "WHERE CAST(fecha_hora_inicio AS date) >= %s ORDER BY fecha_hora_inicio",
        [desde],
    )


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
