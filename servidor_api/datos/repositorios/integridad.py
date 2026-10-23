"""
Verificaciones de integridad entre tablas y esquemas.

La base de datos está dividida por esquemas (citas, clientes, clinica, ventas,
facturacion, inventario) y varias relaciones entre ellos NO tienen llave foránea
(p. ej. ventas.venta.id_cliente). Cada consulta cuenta los registros que rompen
una regla; en una base sana todas deben devolver 0.
"""
from django.db import connection

# (código, descripción, consulta que devuelve las filas que fallan)
VERIFICACIONES = [
    ("stock_vs_movimientos",
     "El stock de cada producto es igual a la suma de sus movimientos de inventario",
     """SELECT p.id_producto, p.codigo, p.stock_actual,
               ISNULL(SUM(CASE m.tipo WHEN N'SALIDA' THEN -m.cantidad ELSE m.cantidad END), 0) AS segun_movimientos
        FROM inventario.producto p
        LEFT JOIN inventario.movimiento_inventario m ON m.id_producto = p.id_producto
        WHERE p.es_servicio = 0
        GROUP BY p.id_producto, p.codigo, p.stock_actual
        HAVING p.stock_actual <> ISNULL(SUM(CASE m.tipo WHEN N'SALIDA' THEN -m.cantidad ELSE m.cantidad END), 0)"""),

    ("servicios_sin_stock",
     "Los servicios no tienen existencias ni movimientos",
     """SELECT p.id_producto, p.codigo FROM inventario.producto p
        WHERE p.es_servicio = 1 AND (p.stock_actual <> 0
              OR EXISTS (SELECT 1 FROM inventario.movimiento_inventario m WHERE m.id_producto = p.id_producto))"""),

    ("subtotal_venta",
     "El subtotal de cada venta es la suma de sus líneas",
     """SELECT v.id_venta, v.subtotal, ISNULL(SUM(d.subtotal), 0) AS suma_lineas
        FROM ventas.venta v LEFT JOIN ventas.detalle_venta d ON d.id_venta = v.id_venta
        GROUP BY v.id_venta, v.subtotal
        HAVING v.subtotal <> ISNULL(SUM(d.subtotal), 0)"""),

    ("venta_cliente_existe",
     "Toda venta pertenece a un cliente existente",
     """SELECT v.id_venta, v.id_cliente FROM ventas.venta v
        WHERE NOT EXISTS (SELECT 1 FROM clientes.cliente c WHERE c.id_cliente = v.id_cliente)"""),

    ("venta_producto_existe",
     "Toda línea de venta apunta a un producto existente",
     """SELECT d.id_detalle, d.id_producto FROM ventas.detalle_venta d
        WHERE NOT EXISTS (SELECT 1 FROM inventario.producto p WHERE p.id_producto = d.id_producto)"""),

    ("venta_pagada_cubierta",
     "Las ventas PAGADAS o ENTREGADAS tienen pagos que cubren el total",
     """SELECT v.id_venta, v.total, ISNULL(SUM(p.monto), 0) AS pagado
        FROM ventas.venta v LEFT JOIN ventas.pago p ON p.id_venta = v.id_venta
        WHERE v.estado IN (N'PAGADA', N'ENTREGADA')
        GROUP BY v.id_venta, v.total
        HAVING ISNULL(SUM(p.monto), 0) < v.total"""),

    ("pagos_no_exceden",
     "Ninguna venta tiene pagos por más de su total",
     """SELECT v.id_venta, v.total, SUM(p.monto) AS pagado
        FROM ventas.venta v JOIN ventas.pago p ON p.id_venta = v.id_venta
        GROUP BY v.id_venta, v.total HAVING SUM(p.monto) > v.total"""),

    ("venta_confirmada_descontada",
     "Cada producto de una venta confirmada tiene su movimiento de SALIDA",
     """SELECT d.id_venta, d.id_producto FROM ventas.detalle_venta d
        JOIN ventas.venta v ON v.id_venta = d.id_venta
        WHERE v.estado IN (N'CONFIRMADA', N'PAGADA', N'ENTREGADA') AND d.es_servicio = 0
          AND NOT EXISTS (SELECT 1 FROM inventario.movimiento_inventario m
                          WHERE m.id_venta = d.id_venta AND m.id_producto = d.id_producto AND m.tipo = N'SALIDA')"""),

    ("factura_total_venta",
     "El total de cada factura emitida es igual al total de su venta",
     """SELECT f.id_factura, f.total, v.total AS total_venta FROM facturacion.factura f
        JOIN ventas.venta v ON v.id_venta = f.id_venta
        WHERE f.estado = N'EMITIDA' AND f.total <> v.total"""),

    ("factura_lineas_suman",
     "Las líneas de cada factura suman su total",
     """SELECT f.id_factura, f.total, ISNULL(SUM(d.total), 0) AS suma_lineas
        FROM facturacion.factura f LEFT JOIN facturacion.factura_detalle d ON d.id_factura = f.id_factura
        GROUP BY f.id_factura, f.total HAVING f.total <> ISNULL(SUM(d.total), 0)"""),

    ("factura_venta_existe",
     "Toda factura corresponde a una venta existente",
     """SELECT f.id_factura, f.id_venta FROM facturacion.factura f
        WHERE NOT EXISTS (SELECT 1 FROM ventas.venta v WHERE v.id_venta = f.id_venta)"""),

    ("cita_cliente_existe",
     "Toda cita pertenece a un cliente existente",
     """SELECT c.id_cita, c.id_cliente FROM citas.cita c
        WHERE NOT EXISTS (SELECT 1 FROM clientes.cliente cl WHERE cl.id_cliente = c.id_cliente)"""),

    ("examen_cliente_existe",
     "Todo examen pertenece a un cliente existente",
     """SELECT e.id_examen, e.id_cliente FROM clinica.examen_visual e
        WHERE NOT EXISTS (SELECT 1 FROM clientes.cliente cl WHERE cl.id_cliente = e.id_cliente)"""),

    ("examen_cita_mismo_paciente",
     "La cita de un examen es del mismo paciente",
     """SELECT e.id_examen, e.id_cliente, c.id_cliente AS cliente_cita FROM clinica.examen_visual e
        JOIN citas.cita c ON c.id_cita = e.id_cita WHERE c.id_cliente <> e.id_cliente"""),

    ("usuario_rol_existe",
     "Todo usuario del sistema tiene un rol existente",
     """SELECT u.id_usuario, u.username FROM seguridad.usuario u
        WHERE NOT EXISTS (SELECT 1 FROM seguridad.rol r WHERE r.id_rol = u.id_rol)"""),
]


def ejecutar():
    """Devuelve una lista de (código, descripción, filas que fallan)."""
    resultados = []
    with connection.cursor() as cursor:
        for codigo, descripcion, sql in VERIFICACIONES:
            cursor.execute(sql)
            resultados.append((codigo, descripcion, cursor.fetchall()))
    return resultados
