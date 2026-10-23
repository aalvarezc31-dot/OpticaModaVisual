from django.urls import path

from .views import (
    autenticacion, catalogos, citas, clientes, examenes, facturas, inicio,
    productos, recetas, reportes, ventas,
)

urlpatterns = [
    path("login/", autenticacion.iniciar_sesion, name="login"),
    path("logout/", autenticacion.cerrar_sesion, name="logout"),

    path("", inicio.inicio, name="inicio"),

    # Clientes
    path("clientes/", clientes.lista_clientes, name="lista_clientes"),
    path("clientes/nuevo/", clientes.registrar_cliente, name="registrar_cliente"),
    path("clientes/<int:id_cliente>/", clientes.detalle_cliente, name="detalle_cliente"),
    path("clientes/<int:id_cliente>/editar/", clientes.editar_cliente, name="editar_cliente"),
    path("clientes/<int:id_cliente>/estado/", clientes.cambiar_activo_cliente,
         name="cambiar_activo_cliente"),

    # Citas
    path("citas/", citas.lista_citas, name="lista_citas"),
    path("citas/nueva/", citas.registrar_cita, name="registrar_cita"),
    path("citas/<int:id_cita>/estado/", citas.cambiar_estado_cita, name="cambiar_estado_cita"),
    path("citas/<int:id_cita>/cobrar/", citas.cobrar_cita, name="cobrar_cita"),

    # Inventario
    path("productos/", productos.lista_productos, name="lista_productos"),
    path("productos/nuevo/", productos.registrar_producto, name="registrar_producto"),
    path("productos/<int:id_producto>/", productos.detalle_producto, name="detalle_producto"),
    path("productos/<int:id_producto>/editar/", productos.editar_producto, name="editar_producto"),
    path("productos/<int:id_producto>/movimiento/", productos.registrar_movimiento,
         name="registrar_movimiento"),
    path("productos/<int:id_producto>/estado/", productos.cambiar_activo_producto,
         name="cambiar_activo_producto"),

    path("proveedores/", catalogos.lista_proveedores, name="lista_proveedores"),
    path("proveedores/nuevo/", catalogos.guardar_proveedor, name="registrar_proveedor"),
    path("proveedores/<int:id_proveedor>/editar/", catalogos.guardar_proveedor,
         name="editar_proveedor"),
    path("proveedores/<int:id_proveedor>/estado/", catalogos.cambiar_activo_proveedor,
         name="cambiar_activo_proveedor"),

    path("catalogos/", catalogos.catalogos_inventario, name="catalogos_inventario"),
    path("catalogos/categorias/nueva/", catalogos.guardar_categoria, name="registrar_categoria"),
    path("catalogos/categorias/<int:id_categoria>/", catalogos.guardar_categoria,
         name="editar_categoria"),
    path("catalogos/marcas/nueva/", catalogos.guardar_marca, name="registrar_marca"),
    path("catalogos/marcas/<int:id_marca>/", catalogos.guardar_marca, name="editar_marca"),

    # Clínica
    path("examenes/", examenes.lista_examenes, name="lista_examenes"),
    path("examenes/nuevo/", examenes.registrar_examen, name="registrar_examen"),
    path("examenes/<int:id_examen>/", examenes.detalle_examen, name="detalle_examen"),

    path("resultados/", recetas.resultados, name="resultados"),
    path("resultados/receta/<int:id_examen>/", recetas.registrar_receta,
         name="registrar_receta"),
    path("recetas/<int:id_receta>/", recetas.ver_receta, name="ver_receta"),

    # Ventas
    path("ventas/", ventas.lista_ventas, name="lista_ventas"),
    path("ventas/nueva/", ventas.nueva_venta, name="nueva_venta"),
    path("ventas/<int:id_venta>/", ventas.detalle_venta, name="detalle_venta"),
    path("ventas/<int:id_venta>/productos/", ventas.agregar_linea, name="agregar_linea_venta"),
    path("ventas/<int:id_venta>/productos/<int:id_detalle>/quitar/", ventas.quitar_linea,
         name="quitar_linea_venta"),
    path("ventas/<int:id_venta>/descuento/", ventas.aplicar_descuento,
         name="descuento_venta"),
    path("ventas/<int:id_venta>/confirmar/", ventas.confirmar_venta, name="confirmar_venta"),
    path("ventas/<int:id_venta>/pagos/", ventas.registrar_pago, name="pago_venta"),
    path("ventas/<int:id_venta>/entregar/", ventas.entregar_venta, name="entregar_venta"),
    path("ventas/<int:id_venta>/anular/", ventas.anular_venta, name="anular_venta"),

    # Facturación
    path("facturas/", facturas.lista_facturas, name="lista_facturas"),
    path("ventas/<int:id_venta>/facturar/", facturas.emitir_factura, name="emitir_factura"),
    path("facturas/<int:id_factura>/", facturas.detalle_factura, name="detalle_factura"),
    path("facturas/<int:id_factura>/anular/", facturas.anular_factura, name="anular_factura"),

    # Reportes
    path("reportes/", reportes.reportes_generales, name="reportes"),
    path("reportes/exportar/<slug:nombre>/", reportes.exportar_reporte, name="exportar_reporte"),
]
