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
