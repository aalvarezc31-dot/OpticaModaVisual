"""Módulo Seguridad: traducción de errores de la BD y permisos por rol."""
from types import SimpleNamespace
from unittest import mock

from django.test import SimpleTestCase

from negocio.excepciones import ReglaNegocioError, desde_error_bd
from negocio.servicios import permisos


class DesdeErrorBD(SimpleTestCase):
    def test_mensaje_de_trigger_se_muestra_tal_cual(self):
        error = Exception(
            "('42000', '[42000] [Microsoft][ODBC Driver 18 for SQL Server][SQL Server]"
            "Stock insuficiente para realizar el movimiento. (50010) (SQLExecDirectW)')"
        )
        resultado = desde_error_bd(error, "No se pudo.")
        self.assertIsInstance(resultado, ReglaNegocioError)
        self.assertEqual(resultado.mensaje, "Stock insuficiente para realizar el movimiento.")

    def test_otro_error_usa_mensaje_por_defecto(self):
        error = Exception("[23000] Violation of UNIQUE KEY constraint (2627)")
        self.assertEqual(desde_error_bd(error, "No se pudo guardar.").mensaje, "No se pudo guardar.")


class PermisosPorRol(SimpleTestCase):
    def usuario(self, superusuario=False, autenticado=True):
        return SimpleNamespace(is_authenticated=autenticado, is_superuser=superusuario)

    def con_rol(self, rol):
        return mock.patch("negocio.servicios.permisos.usuarios.rol_de_cuenta", return_value=rol)

    def test_superusuario_ve_todo(self):
        self.assertEqual(permisos.secciones_permitidas(self.usuario(superusuario=True)), permisos.TODAS)

    def test_optometrista_solo_parte_clinica(self):
        with self.con_rol("OPTOMETRISTA"):
            secciones = permisos.secciones_permitidas(self.usuario())
        self.assertEqual(secciones, {"inicio", "clientes", "citas", "clinica"})
        self.assertNotIn("ventas", secciones)

    def test_vendedor_y_administrador_ven_todo(self):
        for rol in ("VENDEDOR", "ADMINISTRADOR", "administrador"):
            with self.subTest(rol=rol), self.con_rol(rol):
                self.assertEqual(permisos.secciones_permitidas(self.usuario()), permisos.TODAS)

    def test_cuenta_sin_usuario_del_sistema_ve_todo(self):
        with self.con_rol(None):
            self.assertEqual(permisos.secciones_permitidas(self.usuario()), permisos.TODAS)

    def test_anonimo_no_ve_nada(self):
        self.assertEqual(permisos.secciones_permitidas(self.usuario(autenticado=False)), frozenset())

    def test_puede(self):
        with self.con_rol("OPTOMETRISTA"):
            self.assertTrue(permisos.puede(self.usuario(), "clinica"))
            self.assertFalse(permisos.puede(self.usuario(), "facturas"))
            self.assertTrue(permisos.puede(self.usuario(), ""))
