"""Módulo API: serialización, token, catálogo de operaciones y respuestas HTTP."""
import json
from datetime import date, datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest import mock

from django.test import RequestFactory, SimpleTestCase

from api import operaciones, token, views
from api.serializacion import a_json, desde_json
from datos.models import Cliente
from negocio.excepciones import ReglaNegocioError


class Serializacion(SimpleTestCase):
    def test_ida_y_vuelta_de_tipos(self):
        original = {"monto": Decimal("12.50"), "dia": date(2026, 10, 22),
                    "hora": datetime(2026, 10, 22, 9, 30), "lista": (1, "a", None)}
        viaje = json.loads(json.dumps(a_json(original)))
        self.assertEqual(desde_json(viaje), {**original, "lista": [1, "a", None]})

    def test_registro_del_orm_como_diccionario(self):
        cliente = Cliente(id_cliente=3, nombres="Ana", apellidos="López", nit="CF", activo=True,
                          fecha_registro=datetime(2026, 10, 1, 8, 0))
        datos = a_json(cliente)
        self.assertEqual((datos["pk"], datos["nombres"]), (3, "Ana"))
        self.assertEqual(datos["fecha_registro"], {"$fechahora": "2026-10-01T08:00:00"})

    def test_tipo_no_soportado(self):
        with self.assertRaises(TypeError):
            a_json(object())


class CatalogoDeOperaciones(SimpleTestCase):
    def test_todas_las_operaciones_publicadas_existen(self):
        for modulo, (servicio, seccion, publicadas) in operaciones.OPERACIONES.items():
            for operacion in publicadas:
                with self.subTest(op=f"{modulo}.{operacion}"):
                    self.assertTrue(callable(getattr(servicio, operacion)))

    def test_lo_no_publicado_no_se_puede_llamar(self):
        self.assertIsNone(operaciones.buscar("ventas", "_exigir_estado"))
        self.assertIsNone(operaciones.buscar("ventas", "repo_ventas"))
        self.assertIsNone(operaciones.buscar("datos", "listar"))

    def test_cada_modulo_exige_su_seccion(self):
        self.assertEqual(operaciones.buscar("ventas", "crear")[1:], ("ventas", True))
        self.assertEqual(operaciones.buscar("examenes", "registrar")[1], "clinica")


class Token(SimpleTestCase):
    def test_token_valido_y_alterado(self):
        usuario = SimpleNamespace(pk=7)
        firmado = token.emitir(usuario)
        with mock.patch("api.token.get_user_model") as modelo:
            modelo.return_value.objects.filter.return_value.first.return_value = usuario
            self.assertIs(token.usuario_del_token(firmado), usuario)
            modelo.return_value.objects.filter.assert_called_with(pk="7", is_active=True)
            self.assertIsNone(token.usuario_del_token(firmado.replace("7", "8", 1)))
            self.assertIsNone(token.usuario_del_token("basura"))


class EndpointEjecutar(SimpleTestCase):
    def setUp(self):
        self.fabrica = RequestFactory()
        self.usuario = SimpleNamespace(pk=1, is_superuser=True, is_authenticated=True)
        self.token = mock.patch("api.views.token.usuario_del_token", return_value=self.usuario).start()
        self.addCleanup(mock.patch.stopall)

    def llamar(self, modulo="clientes", operacion="buscar", cuerpo=None):
        peticion = self.fabrica.post(f"/api/v1/{modulo}/{operacion}/", data=json.dumps(cuerpo or {}),
                                     content_type="application/json", HTTP_AUTHORIZATION="Token x")
        respuesta = views.ejecutar(peticion, modulo, operacion)
        return respuesta.status_code, json.loads(respuesta.content)

    def con_operacion(self, funcion, seccion="clientes", con_usuario=False):
        mock.patch("api.views.operaciones.buscar", return_value=(funcion, seccion, con_usuario)).start()

    def test_sin_token_401(self):
        self.token.return_value = None
        self.assertEqual(self.llamar()[0], 401)

    def test_operacion_inexistente_404(self):
        self.assertEqual(self.llamar("clientes", "borrar_todo")[0], 404)

    def test_rol_sin_permiso_403(self):
        self.con_operacion(lambda: None, seccion="ventas")
        with mock.patch("api.views.permisos.puede", return_value=False):
            self.assertEqual(self.llamar()[0], 403)

    def test_regla_de_negocio_422_con_campo(self):
        def falla():
            raise ReglaNegocioError("Ya existe un cliente con ese DPI.", campo="dpi")
        self.con_operacion(falla)
        estado, datos = self.llamar()
        self.assertEqual((estado, datos["mensaje"], datos["campo"]), (422, "Ya existe un cliente con ese DPI.", "dpi"))

    def test_argumentos_invalidos_400(self):
        self.con_operacion(lambda a: a)
        self.assertEqual(self.llamar(cuerpo={"args": [1, 2]})[0], 400)

    def test_resultado_y_usuario_inyectado(self):
        recibido = {}

        def suma(user, a, b):
            recibido["user"] = user
            return Decimal(a) + Decimal(b)
        self.con_operacion(suma, con_usuario=True)
        estado, datos = self.llamar(cuerpo={"args": [{"$decimal": "1.25"}, "2"]})
        self.assertEqual((estado, datos["resultado"]), (200, {"$decimal": "3.25"}))
        self.assertIs(recibido["user"], self.usuario)
