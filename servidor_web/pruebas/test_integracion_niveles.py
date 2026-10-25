"""
Pruebas de integración entre niveles (sistema completo):

    navegador (cliente de pruebas) -> servidor web -> HTTP -> servidor API -> SQL Server

Requieren el servidor API encendido sobre la BASE DE PRUEBAS y usuarios de prueba:
    cd servidor_api
    python manage.py preparar_bd_pruebas
    python manage.py crear_usuarios_prueba
    set OPTICA_DB_NAME=OpticaModaVisual_pruebas
    python manage.py runserver 8010
y luego, en otra terminal:
    cd servidor_web
    python manage.py test pruebas.test_integracion_niveles

Si la API no responde, las pruebas se omiten (skip) en lugar de fallar.
"""
import json
import os
import re
import urllib.request
import uuid
from datetime import datetime, timedelta

from django.conf import settings
from django.test import Client, SimpleTestCase, override_settings

CLAVE = os.environ.get("OPTICA_PRUEBAS_CLAVE", "Prueba#2026")
ADMIN = os.environ.get("OPTICA_PRUEBAS_ADMIN", "prueba_admin")
OPTOMETRISTA = os.environ.get("OPTICA_PRUEBAS_OPTOMETRISTA", "prueba_opto")


def _api_disponible():
    try:
        urllib.request.urlopen(settings.URL_API.rstrip("/") + "/api/v1/", timeout=3)
        return True
    except Exception:
        return False


def _id_de(respuesta, patron):
    """Toma el id de la URL a la que redirigió la vista (p. ej. /ventas/15/)."""
    coincidencia = re.search(patron, respuesta["Location"])
    assert coincidencia, f"Redirección inesperada: {respuesta['Location']}"
    return int(coincidencia.group(1))


class IntegracionNiveles(SimpleTestCase):
    """Flujo completo de la óptica a través de los tres niveles."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if not _api_disponible():
            raise cls.skipTest(cls, f"El servidor API no responde en {settings.URL_API}")
        cls.sufijo = uuid.uuid4().hex[:6].upper()

    def setUp(self):
        self.web = Client()
        respuesta = self.web.post("/login/", {"username": ADMIN, "password": CLAVE})
        if respuesta.status_code != 302:
            self.skipTest(f"No se pudo iniciar sesión como {ADMIN} (¿corriste crear_usuarios_prueba?)")

    def texto(self, respuesta):
        return respuesta.content.decode("utf-8", "ignore")

    # --- Sesión y navegación ---

    def test_login_invalido_y_paginas(self):
        anonimo = Client()
        self.assertEqual(anonimo.get("/").status_code, 302)
        r = anonimo.post("/login/", {"username": ADMIN, "password": "incorrecta"})
        self.assertIn("incorrectos", self.texto(r))

        for url in ["/", "/clientes/", "/citas/", "/citas/nueva/", "/examenes/", "/examenes/nuevo/",
                    "/resultados/", "/ventas/", "/ventas/nueva/", "/facturas/", "/productos/",
                    "/productos/nuevo/", "/proveedores/", "/catalogos/", "/reportes/"]:
            with self.subTest(url=url):
                self.assertEqual(self.web.get(url).status_code, 200)

    # --- Flujo clínico + venta + factura ---

    def test_flujo_completo_cita_examen_receta_venta_factura(self):
        # 1. Cliente
        r = self.web.post("/clientes/nuevo/", {
            "nit": "1234567", "nombres": "Integración", "apellidos": f"Niveles {self.sufijo}",
            "telefono": "5555-0000", "genero": "F",
        })
        self.assertEqual(r.status_code, 302, self.texto(r))
        id_cliente = _id_de(r, r"/clientes/(\d+)/")

        # 2. Producto con stock inicial (movimiento ENTRADA por el trigger)
        r = self.web.post("/productos/nuevo/", {
            "codigo": f"T-{self.sufijo}", "nombre": "Montura de integración", "id_categoria": 3,
            "precio_costo": "100.00", "precio_venta": "250.00", "stock_minimo": 1, "stock_inicial": 5,
        })
        self.assertEqual(r.status_code, 302, self.texto(r))
        id_producto = _id_de(r, r"/productos/(\d+)/")
        self.assertIn("<strong>5</strong>", self.texto(self.web.get(f"/productos/{id_producto}/")))

        # 3. Cita en el futuro, confirmada y atendida
        inicio = (datetime.now() + timedelta(days=600, minutes=int(uuid.uuid4().int % 9000))).replace(second=0, microsecond=0)
        r = self.web.post("/citas/nueva/", {
            "id_cliente": id_cliente, "id_tipo_cita": 1,
            "fecha_hora_inicio": inicio.strftime("%Y-%m-%dT%H:%M"), "motivo": "Integración",
        })
        self.assertEqual(r.status_code, 302, self.texto(r))
        lista = self.texto(self.web.get(f"/citas/?q=Niveles {self.sufijo}"))
        id_cita = int(re.search(r"/citas/(\d+)/estado/", lista).group(1))
        self.web.post(f"/citas/{id_cita}/estado/", {"estado": "CONFIRMADA"})
        self.web.post(f"/citas/{id_cita}/estado/", {"estado": "ATENDIDA"})
        self.assertIn("ATENDIDA", self.texto(self.web.get(f"/citas/?q=Niveles {self.sufijo}")))

        # 4. Examen desde la cita y receta
        r = self.web.post("/examenes/nuevo/", {
            "cliente": id_cliente, "cita": id_cita, "optometrista": 1,
            "fecha_examen": datetime.now().strftime("%Y-%m-%dT%H:%M"), "diagnostico": "Miopía leve",
        })
        self.assertEqual(r.status_code, 302, self.texto(r))
        id_examen = _id_de(r, r"/examenes/(\d+)/")
        r = self.web.post(f"/resultados/receta/{id_examen}/", {
            "fecha_emision": datetime.now().date().isoformat(), "od_esfera": "-1.25", "tipo_lente": "Monofocal",
        })
        self.assertEqual(r.status_code, 302, self.texto(r))
        self.assertEqual(self.web.get(r["Location"]).status_code, 200)

        # 5. Venta: cobrar la cita crea la venta con el servicio de examen
        r = self.web.post(f"/citas/{id_cita}/cobrar/")
        id_venta = _id_de(r, r"/ventas/(\d+)/")
        detalle = self.texto(self.web.get(f"/ventas/{id_venta}/"))
        self.assertIn("SV-001", detalle)

        # 6. Producto + confirmación (descuenta stock) + pago completo
        r = self.web.post(f"/ventas/{id_venta}/productos/", {"id_producto": id_producto, "cantidad": 2})
        self.assertEqual(r.status_code, 302, self.texto(r))
        r = self.web.post(f"/ventas/{id_venta}/productos/", {"id_producto": id_producto, "cantidad": 99})
        self.assertIn("Stock insuficiente", self.texto(r))
        self.web.post(f"/ventas/{id_venta}/confirmar/")
        self.assertIn("<strong>3</strong>", self.texto(self.web.get(f"/productos/{id_producto}/")))
        self.assertIn("CONFIRMADA", self.texto(self.web.get(f"/ventas/{id_venta}/")))
        # total = 2 x 250 + 150 (examen visual) = 650
        r = self.web.post(f"/ventas/{id_venta}/pagos/", {"id_metodo_pago": 1, "monto": "650.00",
                                                          "referencia": "VOU-1"})
        self.assertIn("solo admite números", self.texto(r))
        self.web.post(f"/ventas/{id_venta}/pagos/", {"id_metodo_pago": 1, "monto": "650.00"})
        self.assertIn("PAGADA", self.texto(self.web.get(f"/ventas/{id_venta}/")))

        # 7. Factura con IVA calculado por la BD y entrega
        r = self.web.post(f"/ventas/{id_venta}/facturar/", {"nit_receptor": "1234567", "nombre_receptor": "Integración"})
        self.assertEqual(r.status_code, 302, self.texto(r))
        factura = self.texto(self.web.get(r["Location"]))
        self.assertIn("650.00", factura)
        self.assertIn("69.64", factura)  # IVA incluido: 650 - 650 / 1.12
        self.web.post(f"/ventas/{id_venta}/entregar/")
        self.assertIn("ENTREGADA", self.texto(self.web.get(f"/ventas/{id_venta}/")))

        # 8. Venta en dos pasos: carrito primero, luego la orden (descuento antes del total)
        carrito = json.dumps([{"id_producto": id_producto, "cantidad": 1, "descuento": "10"}])
        r = self.web.post("/ventas/nueva/", {"id_cliente": id_cliente, "lineas": "[]"})
        self.assertIn("agrega al menos un producto", self.texto(r))
        r = self.web.post("/ventas/nueva/", {"id_cliente": id_cliente, "lineas": carrito,
                                             "descuento": "15", "confirmar": "on"})
        self.assertEqual(r.status_code, 302, self.texto(r))
        detalle = self.texto(self.web.get(r["Location"]))
        self.assertIn("CONFIRMADA", detalle)
        self.assertIn("225.00", detalle)  # 250 - 10 por línea - 15 general
        self.assertIn("<strong>2</strong>", self.texto(self.web.get(f"/productos/{id_producto}/")))

    def test_reglas_de_negocio_viajan_como_mensajes(self):
        r = self.web.post("/citas/nueva/", {"id_cliente": 1, "id_tipo_cita": 1, "fecha_hora_inicio": "2020-01-01T10:00"},
                          follow=True)
        self.assertIn("Selecciona una fecha y hora futuras", self.texto(r))
        r = self.web.post("/productos/nuevo/", {"codigo": "LO-001", "nombre": "Duplicado", "id_categoria": 1,
                                                "precio_costo": "1", "precio_venta": "2", "stock_minimo": 0})
        self.assertIn("Ya existe un producto con ese código", self.texto(r))

    def test_registro_inexistente_da_404(self):
        self.assertEqual(self.web.get("/ventas/999999/").status_code, 404)

    # --- Analítica ---

    def test_dashboard_y_exportaciones(self):
        r = self.web.get("/reportes/?dias=30")
        self.assertIn("datos-graficas", self.texto(r))
        r = self.web.get("/reportes/?desde=2026-01-01&hasta=2026-01-31")
        self.assertIn("Del 01/01/2026 al 31/01/2026", self.texto(r))
        r = self.web.get("/reportes/?desde=2026-02-01&hasta=2026-01-01")
        self.assertIn("posterior a la fecha fin", self.texto(r))
        r = self.web.get("/reportes/exportar/ventas-por-agente/?desde=2026-01-01&hasta=2026-01-31")
        self.assertTrue(r.content.startswith(b"PK"))
        r = self.web.get("/reportes/exportar/inventario/")
        self.assertEqual(r["Content-Type"], "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        self.assertTrue(r.content.startswith(b"PK"))  # un .xlsx es un ZIP
        r = self.web.get("/reportes/exportar/ventas-diarias/?formato=csv")
        self.assertTrue(r.content.decode("utf-8").startswith("﻿Fecha,Ventas"))
        self.assertEqual(self.web.get("/reportes/exportar/no-existe/").status_code, 404)

    # --- Seguridad entre niveles ---

    def test_optometrista_bloqueado_en_web_y_en_api(self):
        opto = Client()
        r = opto.post("/login/", {"username": OPTOMETRISTA, "password": CLAVE})
        if r.status_code != 302:
            self.skipTest("No existe el usuario optometrista de prueba.")
        self.assertEqual(opto.get("/examenes/").status_code, 200)
        self.assertEqual(opto.get("/ventas/")["Location"], "/")

        # Aun llamando a la API directamente con su token, la API lo rechaza.
        token = opto.session["usuario_api"]["token"]
        peticion = urllib.request.Request(
            settings.URL_API.rstrip("/") + "/api/v1/ventas/buscar/", data=b"{}", method="POST",
            headers={"Authorization": f"Token {token}", "Content-Type": "application/json"},
        )
        with self.assertRaises(urllib.error.HTTPError) as contexto:
            urllib.request.urlopen(peticion, timeout=5)
        self.assertEqual(contexto.exception.code, 403)

    def test_api_sin_token_rechaza(self):
        peticion = urllib.request.Request(
            settings.URL_API.rstrip("/") + "/api/v1/clientes/buscar/", data=b"{}", method="POST",
            headers={"Content-Type": "application/json"},
        )
        with self.assertRaises(urllib.error.HTTPError) as contexto:
            urllib.request.urlopen(peticion, timeout=5)
        self.assertEqual(contexto.exception.code, 401)

    @override_settings(URL_API="http://127.0.0.1:1")
    def test_api_caida_muestra_pagina_503(self):
        r = self.web.get("/clientes/")
        self.assertEqual(r.status_code, 503)
        self.assertIn("No hay conexión con el servidor de aplicación", self.texto(r))
