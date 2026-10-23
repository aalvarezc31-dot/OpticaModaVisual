"""
Integración con SQL Server (sobre la copia OpticaModaVisual_pruebas).

Usa los servicios y repositorios reales, así que ejercita los triggers,
columnas calculadas, secuencias y vistas de la base. Cada prueba corre en
una transacción que se revierte al terminar.
"""
import json
import uuid
from datetime import datetime, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.db import DatabaseError
from django.test import Client, TestCase, TransactionTestCase

from datos.models import Factura, OutboxEvento, Producto, Rol, Usuario, Venta
from datos.repositorios import integridad
from datos.repositorios import inventario as repo_inventario
from datos.repositorios import ventas as repo_ventas
from negocio.excepciones import ReglaNegocioError
from negocio.servicios import (
    citas, clientes, examenes, facturas, productos, recetas, reportes, usuarios, ventas,
)


class BaseIntegracion(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.sufijo = uuid.uuid4().hex[:6].upper()
        cls.admin = User.objects.create_user(f"it_admin_{cls.sufijo}", password="Clave#2026",
                                              is_superuser=True, is_staff=True)
        usuarios.enlazar_cuenta(cls.admin)
        cls.cliente = clientes.registrar({"nit": "CF", "nombres": "Integración",
                                          "apellidos": f"BD {cls.sufijo}", "telefono": None,
                                          "dpi": None, "email": None, "direccion": None,
                                          "genero": None, "fecha_nacimiento": None})

    def nuevo_producto(self, stock=5, servicio=False, precio="250.00"):
        return productos.registrar(self.admin, {
            "codigo": f"IT-{uuid.uuid4().hex[:8].upper()}", "nombre": "Producto de integración",
            "id_categoria": 6 if servicio else 3, "id_marca": None, "id_proveedor": None,
            "modelo": None, "color": None, "material": None, "descripcion": None,
            "es_servicio": servicio, "precio_costo": Decimal("0" if servicio else "100.00"),
            "precio_venta": Decimal(precio), "stock_minimo": 0, "stock_inicial": stock,
        })

    def stock(self, producto):
        return Producto.objects.get(pk=producto.pk).stock_actual


class IntegridadDeDatos(BaseIntegracion):
    def test_todas_las_verificaciones_de_integridad(self):
        for codigo, descripcion, filas in integridad.ejecutar():
            with self.subTest(verificacion=codigo):
                self.assertEqual(list(filas), [], descripcion)


class TriggersDeInventario(BaseIntegracion):
    def test_stock_inicial_se_registra_como_movimiento(self):
        producto = self.nuevo_producto(stock=7)
        self.assertEqual(self.stock(producto), 7)
        self.assertEqual(list(repo_inventario.movimientos_de_producto(producto.pk).values_list("tipo", "cantidad")),
                         [("ENTRADA", 7)])

    def test_ajuste_desde_panel(self):
        producto = self.nuevo_producto(stock=10)
        self.assertEqual(productos.ajustar_stock(self.admin, producto.pk, 4, "Conteo físico"), -6)
        self.assertEqual(self.stock(producto), 4)


class FlujoDeVenta(BaseIntegracion):
    def test_venta_completa_con_triggers_columnas_calculadas_y_factura(self):
        montura = self.nuevo_producto(stock=5)
        consulta = self.nuevo_producto(stock=0, servicio=True, precio="150.00")

        venta = ventas.crear(self.admin, {"id_cliente": self.cliente.pk})
        ventas.agregar_producto(venta.pk, montura.pk, 2)
        ventas.agregar_producto(venta.pk, consulta.pk, 1, precio_unitario=Decimal("120.00"))
        ventas.aplicar_descuento(venta.pk, Decimal("20.00"))

        venta = Venta.objects.get(pk=venta.pk)
        self.assertEqual(venta.subtotal, Decimal("620.00"))  # trigger trg_detalle_venta_aiud
        self.assertEqual(venta.total, Decimal("600.00"))     # columna calculada

        ventas.confirmar(self.admin, venta.pk)
        self.assertEqual(self.stock(montura), 3)
        self.assertTrue(OutboxEvento.objects.filter(id_agregado=str(venta.pk), tipo_evento="VentaConfirmada").exists())

        with self.assertRaisesMessage(ReglaNegocioError, "No se puede modificar"):
            ventas.agregar_producto(venta.pk, montura.pk, 1)

        self.assertFalse(ventas.registrar_pago(self.admin, venta.pk, 1, Decimal("100.00")))
        self.assertTrue(ventas.registrar_pago(self.admin, venta.pk, 2, Decimal("500.00")))
        self.assertEqual(Venta.objects.get(pk=venta.pk).estado, "PAGADA")

        factura = facturas.emitir(self.admin, venta.pk, {"nit_receptor": "cf", "nombre_receptor": "Integración"})
        factura = Factura.objects.get(pk=factura.pk)
        self.assertEqual(factura.total, Decimal("600.00"))
        self.assertEqual(factura.monto_iva, Decimal("64.29"))  # 600 - 600/1.12, calculado por la BD
        self.assertEqual(sum(l.total for l in facturas.ficha(factura.pk)["lineas"]), Decimal("600.00"))
        self.assertEqual(factura.nit_receptor, "CF")

        with self.assertRaisesMessage(ReglaNegocioError, "Primero anula la factura"):
            ventas.anular(self.admin, venta.pk, "Prueba")
        facturas.anular(factura.pk, "Prueba")
        ventas.anular(self.admin, venta.pk, "Prueba")
        self.assertEqual(Venta.objects.get(pk=venta.pk).estado, "ANULADA")
        self.assertEqual(self.stock(montura), 5)  # el inventario regresa
        self.assertTrue(OutboxEvento.objects.filter(id_agregado=str(venta.pk), tipo_evento="VentaAnulada").exists())


class ErroresDeTriggers(TransactionTestCase):
    """
    Pruebas que PROVOCAN el error de un trigger (THROW).

    En SQL Server un THROW dentro de un trigger revierte la transacción
    COMPLETA, no solo el último paso. Por eso estas pruebas no pueden ir
    dentro de la transacción envolvente de TestCase: se ejecutan como en
    producción (una transacción por operación) y borran lo que crean.
    """
    databases = {"default"}

    def _fixture_teardown(self):
        pass  # no vaciar la base de pruebas: es una copia de la real

    def setUp(self):
        self.admin = User.objects.create_user(f"it_trig_{uuid.uuid4().hex[:6]}", is_superuser=True)
        usuarios.enlazar_cuenta(self.admin)
        self.addCleanup(self.admin.delete)
        self.cliente = clientes.registrar({"nit": "CF", "nombres": "Triggers", "apellidos": "Prueba",
                                           "telefono": None, "dpi": None, "email": None, "direccion": None,
                                           "genero": None, "fecha_nacimiento": None})

    def test_trigger_impide_stock_negativo_y_su_mensaje_llega_al_usuario(self):
        producto = BaseIntegracion.nuevo_producto(self, stock=2)
        with self.assertRaisesMessage(ReglaNegocioError, "Stock insuficiente"):
            productos.registrar_movimiento(self.admin, producto.pk, {"tipo": "SALIDA", "cantidad": 3})
        self.assertEqual(Producto.objects.get(pk=producto.pk).stock_actual, 2)

    def test_trigger_impide_reactivar_venta_anulada(self):
        venta = ventas.crear(self.admin, {"id_cliente": self.cliente.pk})
        ventas.anular(self.admin, venta.pk, "Prueba")
        with self.assertRaisesMessage(DatabaseError, "no puede reactivarse"):
            repo_ventas.actualizar(venta.pk, estado="PENDIENTE")
        self.assertEqual(Venta.objects.get(pk=venta.pk).estado, "ANULADA")

    def test_trigger_impide_confirmar_venta_vacia(self):
        venta = ventas.crear(self.admin, {"id_cliente": self.cliente.pk})
        with self.assertRaisesMessage(DatabaseError, "sin productos"):
            repo_ventas.actualizar(venta.pk, estado="CONFIRMADA")
        self.assertEqual(Venta.objects.get(pk=venta.pk).estado, "PENDIENTE")


class FlujoClinico(BaseIntegracion):
    def test_cita_sin_traslape_examen_y_receta(self):
        inicio = (datetime.now() + timedelta(days=900)).replace(second=0, microsecond=0)
        cita = citas.registrar(self.admin, self.cliente.pk, 1, inicio.strftime("%Y-%m-%dT%H:%M"))
        with self.assertRaisesMessage(ReglaNegocioError, "ocupado"):
            citas.registrar(self.admin, self.cliente.pk, 1, (inicio + timedelta(minutes=10)).strftime("%Y-%m-%dT%H:%M"))

        citas.cambiar_estado(cita.pk, "ATENDIDA")
        examen = examenes.registrar({
            "id_cliente": self.cliente.pk, "id_cita": cita.pk, "id_optometrista": 1,
            "fecha_examen": datetime.now(), "motivo_consulta": None, "antecedentes": None,
            "agudeza_visual_od": "20/40", "agudeza_visual_oi": None, "presion_intraocular_od": None,
            "presion_intraocular_oi": None, "diagnostico": "Miopía", "observaciones": None,
        })
        with self.assertRaisesMessage(ReglaNegocioError, "ya tiene un examen"):
            examenes.registrar({"id_cliente": self.cliente.pk, "id_cita": cita.pk, "id_optometrista": 1})

        datos_receta = {campo: None for campo in recetas.CAMPOS_RECETA}
        datos_receta.update(fecha_emision=datetime.now().date(), od_esfera=Decimal("-1.25"))
        receta = recetas.registrar(examen.pk, datos_receta)
        self.assertEqual(recetas.ficha(receta.pk)["cliente"].pk, self.cliente.pk)
        with self.assertRaisesMessage(ReglaNegocioError, "ya tiene una receta"):
            recetas.registrar(examen.pk, datos_receta)


class ReportesSobreVistas(BaseIntegracion):
    def test_tablero_y_todos_los_reportes_exportables(self):
        tablero = reportes.tablero(365)
        for clave in ("ventas_diarias", "por_categoria", "citas_estado", "graficas", "saldo_total"):
            self.assertIn(clave, tablero)
        for nombre in reportes.REPORTES:
            with self.subTest(reporte=nombre):
                titulo, encabezados, filas = reportes.exportacion(nombre, 365)
                self.assertTrue(titulo)
                self.assertTrue(all(len(fila) == len(encabezados) for fila in filas))


class ApiHttpConBD(BaseIntegracion):
    def iniciar(self, cuenta):
        respuesta = Client().post("/api/v1/sesion/", data=json.dumps({"username": cuenta.username,
                                                                      "password": "Clave#2026"}),
                                  content_type="application/json")
        self.assertEqual(respuesta.status_code, 200)
        return respuesta.json()

    def llamar(self, token, ruta, cuerpo=None):
        return Client().post(f"/api/v1/{ruta}/", data=json.dumps(cuerpo or {}),
                             content_type="application/json", HTTP_AUTHORIZATION=f"Token {token}")

    def test_login_y_operacion_por_http(self):
        sesion = self.iniciar(self.admin)
        self.assertIn("ventas", sesion["secciones"])
        respuesta = self.llamar(sesion["token"], "clientes/buscar", {"args": [f"BD {self.sufijo}"]})
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json()["resultado"][0]["id_cliente"], self.cliente.pk)

    def test_optometrista_rechazado_por_la_api(self):
        opto = User.objects.create_user(f"it_opto_{self.sufijo}", password="Clave#2026")
        usuario, _ = usuarios.enlazar_cuenta(opto)
        Usuario.objects.filter(pk=usuario.pk).update(id_rol=Rol.objects.get(nombre="OPTOMETRISTA").pk)

        sesion = self.iniciar(opto)
        self.assertEqual(sorted(sesion["secciones"]), ["citas", "clientes", "clinica", "inicio"])
        self.assertEqual(self.llamar(sesion["token"], "ventas/buscar").status_code, 403)
        self.assertEqual(self.llamar(sesion["token"], "examenes/buscar_con_paciente").status_code, 200)

    def test_credenciales_invalidas(self):
        respuesta = Client().post("/api/v1/sesion/", data=json.dumps({"username": "nadie", "password": "x"}),
                                  content_type="application/json")
        self.assertEqual(respuesta.status_code, 401)
