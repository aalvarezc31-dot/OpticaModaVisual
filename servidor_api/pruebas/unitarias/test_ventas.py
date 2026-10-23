"""Módulo Ventas: productos y servicios, confirmación, pagos, anulación y cobro de citas."""
from decimal import Decimal
from unittest import mock

from django.test import SimpleTestCase

from negocio.excepciones import ReglaNegocioError
from negocio.servicios import ventas
from pruebas.utilidades import producto, registro, sin_transaccion, usuario_web, venta

M = "negocio.servicios.ventas"


class BaseVentas(SimpleTestCase):
    def setUp(self):
        self.repo_ventas = mock.patch(f"{M}.repo_ventas").start()
        self.repo_productos = mock.patch(f"{M}.repo_productos").start()
        self.repo_inventario = mock.patch(f"{M}.repo_inventario").start()
        self.repo_facturas = mock.patch(f"{M}.repo_facturas").start()
        self.repo_citas = mock.patch(f"{M}.repo_citas").start()
        mock.patch(f"{M}.sesion.usuario_actual", return_value=registro(id_usuario=1)).start()
        sin_transaccion(M).start()
        self.addCleanup(mock.patch.stopall)

        self.repo_inventario.SALIDA, self.repo_inventario.ENTRADA = "SALIDA", "ENTRADA"
        self.repo_facturas.EMITIDA = "EMITIDA"
        self.repo_ventas.linea_de_producto.return_value = None
        self.repo_ventas.obtener.return_value = venta()

    def con_venta(self, **campos):
        self.repo_ventas.obtener.return_value = venta(**campos)


class AgregarProducto(BaseVentas):
    def test_producto_a_precio_de_lista(self):
        self.repo_productos.obtener.return_value = producto()
        ventas.agregar_producto(1, 10, 2)
        datos = self.repo_ventas.crear_linea.call_args.kwargs
        self.assertEqual((datos["cantidad"], datos["precio_unitario"]), (2, Decimal("250.00")))

    def test_producto_no_permite_cambiar_precio(self):
        self.repo_productos.obtener.return_value = producto()
        with self.assertRaisesMessage(ReglaNegocioError, "Solo los servicios"):
            ventas.agregar_producto(1, 10, 1, precio_unitario=Decimal("1"))

    def test_servicio_acepta_precio_editado(self):
        self.repo_productos.obtener.return_value = producto(es_servicio=True, stock_actual=0)
        ventas.agregar_producto(1, 10, 1, precio_unitario=Decimal("5800"))
        self.assertEqual(self.repo_ventas.crear_linea.call_args.kwargs["precio_unitario"], Decimal("5800"))

    def test_stock_insuficiente(self):
        self.repo_productos.obtener.return_value = producto(stock_actual=1)
        with self.assertRaisesMessage(ReglaNegocioError, "Stock insuficiente"):
            ventas.agregar_producto(1, 10, 2)

    def test_descuento_no_supera_importe(self):
        self.repo_productos.obtener.return_value = producto()
        with self.assertRaisesMessage(ReglaNegocioError, "descuento"):
            ventas.agregar_producto(1, 10, 1, Decimal("300"))

    def test_producto_repetido_suma_cantidades(self):
        self.repo_productos.obtener.return_value = producto()
        self.repo_ventas.linea_de_producto.return_value = registro(
            id_detalle=4, cantidad=1, descuento=Decimal("0"), precio_unitario=Decimal("250.00"))
        ventas.agregar_producto(1, 10, 2)
        self.repo_ventas.actualizar_linea.assert_called_once_with(4, cantidad=3, descuento=Decimal("0"))

    def test_solo_en_venta_pendiente(self):
        self.con_venta(estado="CONFIRMADA")
        with self.assertRaisesMessage(ReglaNegocioError, "No se puede modificar"):
            ventas.agregar_producto(1, 10, 1)

    def test_producto_inactivo(self):
        self.repo_productos.obtener.return_value = producto(activo=False)
        with self.assertRaisesMessage(ReglaNegocioError, "inactivo"):
            ventas.agregar_producto(1, 10, 1)


class ConfirmarYPagar(BaseVentas):
    def test_confirmar_sin_productos(self):
        self.repo_ventas.lineas.return_value = []
        with self.assertRaisesMessage(ReglaNegocioError, "al menos un producto"):
            ventas.confirmar(usuario_web(), 1)

    def test_confirmar_descuenta_solo_productos(self):
        self.repo_ventas.lineas.return_value = [
            registro(id_producto=10, cantidad=2, es_servicio=False),
            registro(id_producto=99, cantidad=1, es_servicio=True),
        ]
        ventas.confirmar(usuario_web(), 1)
        self.repo_inventario.crear_movimiento.assert_called_once()
        mov = self.repo_inventario.crear_movimiento.call_args.kwargs
        self.assertEqual((mov["id_producto"], mov["tipo"], mov["cantidad"]), (10, "SALIDA", 2))
        self.repo_ventas.actualizar.assert_called_with(1, estado="CONFIRMADA")

    def test_pago_parcial_y_pago_completo(self):
        self.con_venta(estado="CONFIRMADA", total=Decimal("650.00"))
        self.repo_ventas.total_pagado.return_value = Decimal("0")
        self.assertFalse(ventas.registrar_pago(usuario_web(), 1, 1, Decimal("300")))
        self.repo_ventas.total_pagado.return_value = Decimal("300")
        self.assertTrue(ventas.registrar_pago(usuario_web(), 1, 1, Decimal("350")))
        self.repo_ventas.actualizar.assert_called_with(1, estado="PAGADA")

    def test_pago_mayor_al_saldo(self):
        self.con_venta(estado="CONFIRMADA", total=Decimal("100.00"))
        self.repo_ventas.total_pagado.return_value = Decimal("0")
        with self.assertRaisesMessage(ReglaNegocioError, "supera el saldo"):
            ventas.registrar_pago(usuario_web(), 1, 1, Decimal("100.01"))

    def test_no_se_cobra_venta_pendiente(self):
        with self.assertRaisesMessage(ReglaNegocioError, "No se puede cobrar"):
            ventas.registrar_pago(usuario_web(), 1, 1, Decimal("10"))


class Anular(BaseVentas):
    def test_entregada_no_se_anula(self):
        self.con_venta(estado="ENTREGADA")
        with self.assertRaisesMessage(ReglaNegocioError, "No se puede anular"):
            ventas.anular(usuario_web(), 1, "x")

    def test_exige_motivo(self):
        with self.assertRaisesMessage(ReglaNegocioError, "motivo"):
            ventas.anular(usuario_web(), 1, "  ")

    def test_factura_vigente_bloquea(self):
        self.repo_facturas.de_venta.return_value = registro(estado="EMITIDA", serie="A", numero=8)
        with self.assertRaisesMessage(ReglaNegocioError, "Primero anula la factura A-8"):
            ventas.anular(usuario_web(), 1, "Error")

    def test_confirmada_devuelve_stock(self):
        self.con_venta(estado="CONFIRMADA")
        self.repo_facturas.de_venta.return_value = None
        self.repo_ventas.lineas.return_value = [registro(id_producto=10, cantidad=2, es_servicio=False)]
        ventas.anular(usuario_web(), 1, "Desistió")
        mov = self.repo_inventario.crear_movimiento.call_args.kwargs
        self.assertEqual((mov["tipo"], mov["cantidad"]), ("ENTRADA", 2))
        self.assertIn("ANULADA: Desistió", self.repo_ventas.actualizar.call_args.kwargs["observaciones"])


class CobrarCita(BaseVentas):
    def test_cita_cancelada_no_se_cobra(self):
        self.repo_citas.obtener.return_value = registro(estado="CANCELADA")
        with self.assertRaisesMessage(ReglaNegocioError, "No se cobra"):
            ventas.cobrar_cita(usuario_web(), 3)

    def test_reutiliza_la_venta_existente(self):
        self.repo_citas.obtener.return_value = registro(estado="ATENDIDA")
        self.repo_ventas.de_cita.return_value = registro(id_venta=15)
        resultado, mensaje = ventas.cobrar_cita(usuario_web(), 3)
        self.assertEqual(resultado.id_venta, 15)
        self.assertIn("ya tiene la venta #15", mensaje)

    def test_servicio_segun_tipo_de_cita(self):
        self.assertEqual(ventas.SERVICIO_POR_TIPO_CITA["EXAMEN VISUAL"], "SV-001")
        self.assertNotIn("ENTREGA DE LENTES", ventas.SERVICIO_POR_TIPO_CITA)
