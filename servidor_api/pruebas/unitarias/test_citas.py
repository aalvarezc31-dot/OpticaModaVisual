"""Módulo Citas: registro con validaciones de horario y cambios de estado."""
from datetime import timedelta
from unittest import mock

from django.test import SimpleTestCase
from django.utils import timezone

from datos.models import Cliente
from negocio.excepciones import ReglaNegocioError
from negocio.servicios import citas
from pruebas.utilidades import registro, usuario_web

M = "negocio.servicios.citas"


class RegistrarCita(SimpleTestCase):
    def setUp(self):
        self.repo_citas = mock.patch(f"{M}.repo_citas").start()
        self.repo_clientes = mock.patch(f"{M}.repo_clientes").start()
        self.repo_usuarios = mock.patch(f"{M}.repo_usuarios").start()
        mock.patch(f"{M}.sesion.usuario_actual", return_value=registro(id_usuario=1)).start()
        self.addCleanup(mock.patch.stopall)
        self.repo_citas.PROGRAMADA = "PROGRAMADA"

        self.repo_clientes.obtener.return_value = registro(
            id_cliente=7, nombres="Ana", apellidos="López", telefono="5555-1234", activo=True)
        self.repo_citas.obtener_tipo_activo.return_value = registro(id_tipo_cita=1, duracion_minutos=30)
        self.repo_citas.existe_traslape.return_value = False
        self.manana = (timezone.now() + timedelta(days=1)).replace(second=0, microsecond=0)

    def registrar(self, fecha=None, **extra):
        return citas.registrar(usuario_web(), id_cliente="7", id_tipo_cita="1",
                               fecha_txt=(fecha or self.manana).strftime("%Y-%m-%dT%H:%M"), **extra)

    def test_registra_programada_y_calcula_fin_segun_tipo(self):
        self.registrar(motivo="  Control  ")
        datos = self.repo_citas.crear.call_args.kwargs
        self.assertEqual(datos["estado"], "PROGRAMADA")
        self.assertEqual(datos["fecha_hora_fin"] - datos["fecha_hora_inicio"], timedelta(minutes=30))
        self.assertEqual(datos["cliente_nombre"], "Ana López")
        self.assertEqual(datos["motivo"], "Control")

    def test_rechaza_fecha_pasada(self):
        with self.assertRaisesMessage(ReglaNegocioError, "futuras"):
            self.registrar(fecha=timezone.now() - timedelta(hours=1))
        self.repo_citas.crear.assert_not_called()

    def test_rechaza_horario_ocupado(self):
        self.repo_citas.existe_traslape.return_value = True
        with self.assertRaisesMessage(ReglaNegocioError, "ocupado"):
            self.registrar()

    def test_rechaza_paciente_inactivo(self):
        self.repo_clientes.obtener.return_value.activo = False
        with self.assertRaisesMessage(ReglaNegocioError, "inactivo"):
            self.registrar()

    def test_datos_invalidos_dan_mensaje_general(self):
        self.repo_clientes.obtener.side_effect = Cliente.DoesNotExist
        with self.assertRaisesMessage(ReglaNegocioError, "Revisa los datos"):
            self.registrar()
        with self.assertRaisesMessage(ReglaNegocioError, "Revisa los datos"):
            citas.registrar(usuario_web(), "x", "1", "2030-01-01T10:00")


class CambiarEstado(SimpleTestCase):
    def setUp(self):
        self.repo = mock.patch(f"{M}.repo_citas").start()
        self.repo.PROGRAMADA, self.repo.CONFIRMADA = "PROGRAMADA", "CONFIRMADA"
        self.repo.ATENDIDA, self.repo.CANCELADA, self.repo.NO_ASISTIO = "ATENDIDA", "CANCELADA", "NO_ASISTIO"
        self.addCleanup(mock.patch.stopall)

    def con_estado(self, estado):
        self.repo.obtener.return_value = registro(id_cita=3, estado=estado)

    def test_transiciones_permitidas(self):
        self.con_estado("Programada")  # datos antiguos en minúsculas también funcionan
        self.assertEqual(citas.acciones_disponibles(self.repo.obtener.return_value),
                         ["CONFIRMADA", "ATENDIDA", "NO_ASISTIO", "CANCELADA"])
        citas.cambiar_estado(3, "CONFIRMADA")
        self.repo.actualizar.assert_called_once_with(3, estado="CONFIRMADA")

    def test_cita_atendida_no_se_puede_cancelar(self):
        self.con_estado("ATENDIDA")
        with self.assertRaisesMessage(ReglaNegocioError, "no puede pasar"):
            citas.cambiar_estado(3, "CANCELADA", "x")

    def test_cancelar_exige_motivo_y_lo_recorta(self):
        self.con_estado("PROGRAMADA")
        with self.assertRaisesMessage(ReglaNegocioError, "motivo"):
            citas.cambiar_estado(3, "CANCELADA", "   ")
        citas.cambiar_estado(3, "CANCELADA", "x" * 300)
        self.assertEqual(len(self.repo.actualizar.call_args.kwargs["motivo_cancelacion"]), 255)
