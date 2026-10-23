"""Cliente HTTP de la API: codificación de datos y traducción de errores."""
import io
import json
import urllib.error
from datetime import date, datetime
from decimal import Decimal
from unittest import mock

from django.test import SimpleTestCase

from presentacion import cliente_api
from presentacion.servicios import clientes


def respuesta_json(datos):
    respuesta = mock.MagicMock()
    respuesta.read.return_value = json.dumps(datos).encode()
    respuesta.__enter__.return_value = respuesta
    return respuesta


def error_http(codigo, datos):
    return urllib.error.HTTPError("http://api", codigo, "x", {}, io.BytesIO(json.dumps(datos).encode()))


class Codificacion(SimpleTestCase):
    def test_ida_y_vuelta(self):
        original = {"monto": Decimal("9.90"), "dia": date(2026, 10, 23),
                    "momento": datetime(2026, 10, 23, 8, 15), "lista": [1, {"n": Decimal("1")}]}
        self.assertEqual(cliente_api.decodificar(json.loads(json.dumps(cliente_api.codificar(original)))), original)

    def test_registro_se_lee_como_objeto_y_como_diccionario(self):
        registro = cliente_api.decodificar({"nombres": "Ana", "total": {"$decimal": "5.00"}})
        self.assertEqual((registro.nombres, registro["nombres"], registro.total), ("Ana", "Ana", Decimal("5.00")))
        registro.extra = 1
        self.assertEqual(registro["extra"], 1)
        with self.assertRaises(AttributeError):
            registro.no_existe


class Peticiones(SimpleTestCase):
    def setUp(self):
        self.urlopen = mock.patch("presentacion.cliente_api.urllib.request.urlopen").start()
        self.addCleanup(mock.patch.stopall)

    def test_llamada_envia_token_y_argumentos(self):
        self.urlopen.return_value = respuesta_json({"resultado": [{"id_cliente": 1}]})
        marca = cliente_api.token_actual.set("abc")
        try:
            resultado = clientes.buscar("Ana", estado="todos")
        finally:
            cliente_api.token_actual.reset(marca)

        peticion = self.urlopen.call_args.args[0]
        self.assertTrue(peticion.full_url.endswith("/api/v1/clientes/buscar/"))
        self.assertEqual(peticion.get_header("Authorization"), "Token abc")
        self.assertEqual(json.loads(peticion.data), {"args": ["Ana"], "kwargs": {"estado": "todos"}})
        self.assertEqual(resultado[0].id_cliente, 1)

    def test_errores_http_se_traducen(self):
        casos = [(401, cliente_api.SesionVencida), (403, cliente_api.SinPermiso),
                 (404, cliente_api.RecursoNoEncontrado), (422, cliente_api.ReglaNegocioError)]
        for codigo, clase in casos:
            with self.subTest(codigo=codigo):
                self.urlopen.side_effect = error_http(codigo, {"mensaje": "Mensaje", "campo": "dpi"})
                with self.assertRaises(clase) as contexto:
                    clientes.obtener(1)
                self.assertEqual((contexto.exception.mensaje, contexto.exception.campo), ("Mensaje", "dpi"))

    def test_api_caida(self):
        self.urlopen.side_effect = urllib.error.URLError("rechazada")
        with self.assertRaises(cliente_api.ServidorNoDisponible):
            clientes.obtener(1)

    def test_operaciones_privadas_no_se_exponen(self):
        with self.assertRaises(AttributeError):
            clientes._interna
