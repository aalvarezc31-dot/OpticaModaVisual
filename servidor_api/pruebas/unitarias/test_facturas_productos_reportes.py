"""Módulos Facturación, Inventario, Clientes, Panel y Reportes."""
from datetime import date
from decimal import Decimal
from unittest import mock

from django.test import SimpleTestCase

from negocio.excepciones import ReglaNegocioError
from negocio.servicios import clientes, facturas, panel, productos, reportes
from pruebas.utilidades import producto, registro, usuario_web, venta


class ProrrateoFactura(SimpleTestCase):
    def lineas(self, *subtotales):
        return [registro(subtotal=Decimal(s)) for s in subtotales]

    def test_reparte_el_descuento_y_cuadra_exacto(self):
        repartos = facturas._prorratear(Decimal("25.00"), self.lineas("500", "150", "100"))
        self.assertEqual(sum(repartos), Decimal("25.00"))
        self.assertEqual(repartos[0], Decimal("16.67"))

    def test_sin_descuento(self):
        self.assertEqual(facturas._prorratear(Decimal("0"), self.lineas("10", "20")), [0, 0])

    def test_una_linea_recibe_todo(self):
        self.assertEqual(facturas._prorratear(Decimal("7.50"), self.lineas("100")), [Decimal("7.50")])


class EmitirFactura(SimpleTestCase):
    def setUp(self):
        self.obtener = mock.patch("negocio.servicios.facturas.ventas.obtener").start()
        self.repo = mock.patch("negocio.servicios.facturas.repo_facturas").start()
        self.addCleanup(mock.patch.stopall)

    def test_venta_pendiente_no_se_factura(self):
        self.obtener.return_value = venta(estado="PENDIENTE")
        with self.assertRaisesMessage(ReglaNegocioError, "Solo se facturan"):
            facturas.emitir(usuario_web(), 1, {})

    def test_una_factura_por_venta(self):
        self.obtener.return_value = venta(estado="PAGADA")
        self.repo.de_venta.return_value = registro(id_factura=1)
        with self.assertRaisesMessage(ReglaNegocioError, "ya tiene una factura"):
            facturas.emitir(usuario_web(), 1, {})

    def test_anular_exige_motivo_y_estado_emitida(self):
        self.repo.obtener.return_value = registro(estado="EMITIDA")
        with self.assertRaisesMessage(ReglaNegocioError, "motivo"):
            facturas.anular(1, "")
        self.repo.obtener.return_value = registro(estado="ANULADA")
        with self.assertRaisesMessage(ReglaNegocioError, "ya está anulada"):
            facturas.anular(1, "x")


class Inventario(SimpleTestCase):
    def setUp(self):
        self.repo = mock.patch("negocio.servicios.productos.repo_productos").start()
        self.inventario = mock.patch("negocio.servicios.productos.repo_inventario").start()
        mock.patch("negocio.servicios.productos.sesion.usuario_actual",
                   return_value=registro(id_usuario=1)).start()
        mock.patch("negocio.servicios.productos.transaction.atomic",
                   lambda *a, **k: mock.MagicMock()).start()
        self.addCleanup(mock.patch.stopall)
        self.inventario.ENTRADA, self.inventario.SALIDA, self.inventario.AJUSTE = "ENTRADA", "SALIDA", "AJUSTE"
        self.repo.codigo_en_uso.return_value = False

    def datos(self, **extra):
        return {"codigo": "MO-9", "precio_costo": Decimal("100"), "precio_venta": Decimal("200"), **extra}

    def test_codigo_duplicado(self):
        self.repo.codigo_en_uso.return_value = True
        with self.assertRaisesMessage(ReglaNegocioError, "Ya existe un producto"):
            productos.validar(self.datos())

    def test_precio_venta_menor_al_costo(self):
        with self.assertRaisesMessage(ReglaNegocioError, "menor que el costo"):
            productos.validar(self.datos(precio_venta=Decimal("50")))

    def test_movimientos_invalidos(self):
        self.repo.obtener.return_value = producto(es_servicio=True)
        with self.assertRaisesMessage(ReglaNegocioError, "servicios no manejan"):
            productos.registrar_movimiento(usuario_web(), 10, {"tipo": "ENTRADA", "cantidad": 1})
        self.repo.obtener.return_value = producto()
        with self.assertRaisesMessage(ReglaNegocioError, "mayor que cero"):
            productos.registrar_movimiento(usuario_web(), 10, {"tipo": "SALIDA", "cantidad": 0})
        with self.assertRaisesMessage(ReglaNegocioError, "no puede ser cero"):
            productos.registrar_movimiento(usuario_web(), 10, {"tipo": "AJUSTE", "cantidad": 0})

    def test_ajustar_stock_registra_la_diferencia(self):
        self.repo.obtener.return_value = producto(stock_actual=5)
        self.assertEqual(productos.ajustar_stock(usuario_web(), 10, 5), 0)
        self.inventario.crear_movimiento.assert_not_called()
        self.assertEqual(productos.ajustar_stock(usuario_web(), 10, 2, "Conteo"), -3)
        mov = self.inventario.crear_movimiento.call_args.kwargs
        self.assertEqual((mov["tipo"], mov["cantidad"], mov["motivo"]), ("AJUSTE", -3, "Conteo"))
        with self.assertRaisesMessage(ReglaNegocioError, "negativas"):
            productos.ajustar_stock(usuario_web(), 10, -1)


class Clientes(SimpleTestCase):
    @mock.patch("negocio.servicios.clientes.repo_clientes")
    def test_dpi_duplicado(self, repo):
        repo.dpi_en_uso.return_value = True
        with self.assertRaisesMessage(ReglaNegocioError, "DPI"):
            clientes.registrar({"dpi": "1234567890123"})
        repo.crear.assert_not_called()

    @mock.patch("negocio.servicios.clientes.repo_clientes")
    def test_registra_activo(self, repo):
        repo.dpi_en_uso.return_value = False
        clientes.registrar({"dpi": None, "nombres": "Ana"})
        self.assertTrue(repo.crear.call_args.kwargs["activo"])


class PanelYReportes(SimpleTestCase):
    @mock.patch("negocio.servicios.panel.repo_citas")
    def test_actividad_semanal_en_porcentajes(self, repo):
        repo.contar_del_dia.side_effect = [0, 2, 4, 1, 0, 0, 4]
        actividad = panel._actividad_semana(date(2026, 10, 22))
        self.assertEqual(len(actividad), 7)
        self.assertEqual([d["porcentaje"] for d in actividad], [8, 50, 100, 25, 8, 8, 100])
        self.assertEqual(actividad[-1]["etiqueta"], "Jue")

    def test_periodos_validos(self):
        self.assertEqual(reportes.normalizar_dias("90"), 90)
        self.assertEqual(reportes.normalizar_dias("13"), 30)
        self.assertEqual(reportes.normalizar_dias(None), 30)

    def test_exportacion_respeta_columnas(self):
        self.assertIsNone(reportes.exportacion("no-existe", 30))
        with mock.patch("negocio.servicios.reportes.repo_reportes.ventas_por_vendedor",
                        return_value=[{"vendedor_nombre": "Ana", "cantidad_ventas": 2, "total_vendido": Decimal("90")}]):
            titulo, encabezados, filas = reportes.exportacion("ventas-por-vendedor", 30)
        self.assertEqual(titulo, "Ventas por vendedor")
        self.assertEqual(encabezados, ["Vendedor", "Ventas", "Total (Q)"])
        self.assertEqual(filas, [["Ana", 2, Decimal("90")]])

    def test_hay_al_menos_dos_reportes_exportables(self):
        self.assertGreaterEqual(len(reportes.REPORTES), 2)
