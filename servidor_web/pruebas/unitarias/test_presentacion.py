"""Formularios, permisos del menú, sesión y exportación (sin API)."""
import io
from datetime import date, timedelta
from decimal import Decimal
from unittest import mock

from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.backends.signed_cookies import SessionStore
from django.test import RequestFactory, SimpleTestCase

from presentacion import sesion
from presentacion.cliente_api import Registro
from presentacion.context_processors import seccion_de_ruta
from presentacion.exportar import respuesta_csv, respuesta_xlsx
from presentacion.forms import ClienteForm, ProductoForm, RecetaOpticaForm
from presentacion.middleware import PermisosPorRolMiddleware


class FormularioCliente(SimpleTestCase):
    def form(self, **datos):
        return ClienteForm({"nombres": "Ana", "apellidos": "López", "nit": "cf", **datos})

    def test_valido_y_normaliza(self):
        form = self.form(telefono="5555-1234")
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["nit"], "CF")
        self.assertIsNone(form.cleaned_data["dpi"])

    def test_validaciones(self):
        casos = {
            "dpi": {"dpi": "123"},
            "telefono": {"telefono": "abc"},
            "fecha_nacimiento": {"fecha_nacimiento": (date.today() + timedelta(days=1)).isoformat()},
            "email": {"email": "no-es-correo"},
            "telefono_corto": {"telefono": "5555-12"},
            "email_sin_dominio": {"email": "ana@optica"},
            "nombres": {"nombres": "   "},
        }
        for caso, datos in casos.items():
            campo = next(iter(datos))
            with self.subTest(caso=caso):
                form = self.form(**datos)
                self.assertFalse(form.is_valid())
                self.assertIn(campo, form.errors)

    def test_html_valida_en_el_navegador(self):
        html = str(self.form()["telefono"]) + str(self.form()["email"])
        self.assertIn('pattern="', html)
        self.assertIn('minlength="8"', html)


class FormularioReceta(SimpleTestCase):
    def test_vencimiento_no_antes_de_emision(self):
        form = RecetaOpticaForm({"fecha_emision": "2026-10-23", "fecha_vencimiento": "2026-10-01"})
        self.assertFalse(form.is_valid())
        self.assertIn("fecha_vencimiento", form.errors)

    def test_eje_entre_0_y_180(self):
        form = RecetaOpticaForm({"fecha_emision": "2026-10-23", "od_eje": "181"})
        self.assertIn("od_eje", form.errors)


class FormularioProducto(SimpleTestCase):
    def setUp(self):
        catalogo = {"categorias": [Registro(id_categoria=3, nombre="MONTURA")],
                    "marcas": [Registro(id_marca=1, nombre="Genérico")],
                    "proveedores": []}
        mock.patch("presentacion.forms.productos.productos.opciones_catalogo", return_value=catalogo).start()
        self.addCleanup(mock.patch.stopall)

    def test_opciones_vienen_de_la_api_y_codigo_en_mayusculas(self):
        form = ProductoForm({"codigo": " mo-1 ", "nombre": "Montura", "id_categoria": "3", "id_marca": "",
                             "precio_costo": "10", "precio_venta": "20", "stock_minimo": "0"})
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual((form.cleaned_data["codigo"], form.cleaned_data["id_marca"]), ("MO-1", None))

    def test_al_editar_no_hay_stock_inicial(self):
        self.assertNotIn("stock_inicial", ProductoForm(nuevo=False).fields)


class PermisosEnElMenu(SimpleTestCase):
    def test_seccion_de_cada_ruta(self):
        self.assertEqual(seccion_de_ruta("/"), "inicio")
        self.assertEqual(seccion_de_ruta("/resultados/receta/4/"), "clinica")
        self.assertEqual(seccion_de_ruta("/citas/5/estado/"), "citas")
        self.assertEqual(seccion_de_ruta("/citas/5/cobrar/"), "ventas")
        self.assertEqual(seccion_de_ruta("/catalogos/"), "inventario")

    def peticion(self, ruta, secciones):
        peticion = RequestFactory().get(ruta)
        peticion.session = SessionStore()
        peticion._messages = FallbackStorage(peticion)
        peticion.user = sesion.UsuarioWeb({"token": "t", "usuario": {"username": "opto"}, "secciones": secciones})
        return PermisosPorRolMiddleware(lambda r: "pasa")(peticion)

    def test_optometrista_redirigido_fuera_de_ventas(self):
        clinica = ["inicio", "clientes", "citas", "clinica"]
        self.assertEqual(self.peticion("/examenes/", clinica), "pasa")
        respuesta = self.peticion("/ventas/", clinica)
        self.assertEqual((respuesta.status_code, respuesta["Location"]), (302, "/"))


class Sesion(SimpleTestCase):
    def test_usuario_web(self):
        anonimo = sesion.UsuarioWeb()
        self.assertFalse(anonimo.is_authenticated)
        usuario = sesion.UsuarioWeb({"token": "x", "usuario": {"username": "ana", "is_staff": True},
                                     "rol": "VENDEDOR", "secciones": ["ventas"]})
        self.assertTrue(usuario.is_authenticated and usuario.is_staff)
        self.assertEqual((usuario.get_username(), usuario.secciones), ("ana", frozenset({"ventas"})))

    def test_login_required_redirige(self):
        peticion = RequestFactory().get("/ventas/")
        peticion.user = sesion.UsuarioWeb()
        respuesta = sesion.login_required(lambda r: "vista")(peticion)
        self.assertEqual(respuesta["Location"], "/login/?next=%2Fventas%2F")


class Exportacion(SimpleTestCase):
    encabezados = ["Fecha", "Cliente", "Total (Q)"]
    filas = [[date(2026, 10, 23), "Ana López", Decimal("650.00")]]

    def test_csv_con_bom_para_excel(self):
        respuesta = respuesta_csv("Ventas", self.encabezados, self.filas)
        texto = respuesta.content.decode("utf-8")
        self.assertTrue(texto.startswith("﻿Fecha,Cliente,Total (Q)"))
        self.assertIn("23/10/2026,Ana López,650.00", texto)
        self.assertIn("attachment", respuesta["Content-Disposition"])

    def test_excel_con_formato(self):
        from openpyxl import load_workbook
        respuesta = respuesta_xlsx("Ventas", self.encabezados, self.filas)
        hoja = load_workbook(io.BytesIO(respuesta.content)).active
        self.assertEqual(hoja["A4"].value, "Fecha")
        self.assertEqual(hoja["C5"].value, 650.0)
        self.assertEqual(hoja["C5"].number_format, '"Q" #,##0.00')
        self.assertTrue(hoja["A4"].font.bold)
