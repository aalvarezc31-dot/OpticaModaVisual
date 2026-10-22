from datetime import datetime, timedelta

from django.utils import timezone

from datos.models import Cita, Cliente, TipoCita, Usuario
from datos.repositorios import citas as repo_citas
from datos.repositorios import clientes as repo_clientes
from datos.repositorios import usuarios as repo_usuarios
from negocio.excepciones import RecursoNoEncontrado, ReglaNegocioError
from negocio.servicios import sesion

ESTADOS = [
    (repo_citas.PROGRAMADA, "Programada"),
    (repo_citas.CONFIRMADA, "Confirmada"),
    (repo_citas.ATENDIDA, "Atendida"),
    (repo_citas.NO_ASISTIO, "No asistió"),
    (repo_citas.CANCELADA, "Cancelada"),
]

# Desde qué estado se puede pasar a cuál.
TRANSICIONES = {
    repo_citas.PROGRAMADA: [repo_citas.CONFIRMADA, repo_citas.ATENDIDA,
                            repo_citas.NO_ASISTIO, repo_citas.CANCELADA],
    repo_citas.CONFIRMADA: [repo_citas.ATENDIDA, repo_citas.NO_ASISTIO,
                            repo_citas.CANCELADA],
}

MENSAJE_DATOS_INVALIDOS = (
    "No se pudo registrar la cita. Revisa los datos y el horario."
)


def buscar(busqueda="", estado="", fecha=None):
    return repo_citas.listar(busqueda, estado, fecha)


def citas_para_examen():
    return repo_citas.listar_recientes_primero()


def obtener(id_cita):
    try:
        return repo_citas.obtener(id_cita)
    except Cita.DoesNotExist:
        raise RecursoNoEncontrado("La cita no existe.")


def opciones_formulario():
    return {
        "clientes": repo_clientes.listar_por_nombre(),
        "tipos": repo_citas.listar_tipos_activos(),
        "optometristas": repo_usuarios.listar_activos(),
    }


def acciones_disponibles(cita):
    return TRANSICIONES.get(cita.estado.upper(), [])


def _convertir_fecha(fecha_txt):
    fecha_inicio = datetime.fromisoformat(fecha_txt.strip())

    # Con USE_TZ = False todas las fechas son hora local sin zona.
    if timezone.is_aware(fecha_inicio):
        fecha_inicio = timezone.make_naive(fecha_inicio)

    return fecha_inicio


def registrar(user, id_cliente, id_tipo_cita, fecha_txt, motivo="",
              id_optometrista=""):
    """
    Registra una cita PROGRAMADA.

    Reglas: el paciente debe estar activo, la fecha debe ser futura y el
    horario no puede traslaparse con otra cita vigente.
    """
    registra = sesion.usuario_actual(user)

    try:
        cliente = repo_clientes.obtener(int(id_cliente))
        tipo = repo_citas.obtener_tipo_activo(int(id_tipo_cita))
        fecha_inicio = _convertir_fecha(fecha_txt)
        optometrista = (
            repo_usuarios.obtener_activo(int(id_optometrista))
            if id_optometrista else None
        )
    except (
        ValueError,
        TypeError,
        Cliente.DoesNotExist,
        TipoCita.DoesNotExist,
        Usuario.DoesNotExist,
    ):
        raise ReglaNegocioError(MENSAJE_DATOS_INVALIDOS)

    if not cliente.activo:
        raise ReglaNegocioError("El paciente está inactivo.")

    if fecha_inicio <= timezone.now():
        raise ReglaNegocioError("Selecciona una fecha y hora futuras.")

    fecha_fin = fecha_inicio + timedelta(minutes=tipo.duracion_minutos)

    if repo_citas.existe_traslape(fecha_inicio, fecha_fin):
        raise ReglaNegocioError("Ese horario ya está ocupado.")

    return repo_citas.crear(
        id_tipo_cita=tipo.id_tipo_cita,
        id_cliente=cliente.id_cliente,
        cliente_nombre=f"{cliente.nombres} {cliente.apellidos}",
        cliente_telefono=cliente.telefono or None,
        id_usuario_atiende=optometrista.id_usuario if optometrista else None,
        usuario_atiende_nombre=(
            sesion.nombre_completo(optometrista) if optometrista else None
        ),
        fecha_hora_inicio=fecha_inicio,
        fecha_hora_fin=fecha_fin,
        estado=repo_citas.PROGRAMADA,
        motivo=(motivo or "").strip() or None,
        motivo_cancelacion=None,
        id_usuario_registra=registra.id_usuario,
        fecha_registro=timezone.now(),
    )


def cambiar_estado(id_cita, nuevo_estado, motivo_cancelacion=""):
    cita = obtener(id_cita)

    if nuevo_estado not in acciones_disponibles(cita):
        raise ReglaNegocioError(
            f"Una cita en estado {cita.estado} no puede pasar a {nuevo_estado}."
        )

    datos = {"estado": nuevo_estado}

    if nuevo_estado == repo_citas.CANCELADA:
        motivo = (motivo_cancelacion or "").strip()
        if not motivo:
            raise ReglaNegocioError("Indica el motivo de la cancelación.")
        datos["motivo_cancelacion"] = motivo[:255]

    repo_citas.actualizar(id_cita, **datos)
