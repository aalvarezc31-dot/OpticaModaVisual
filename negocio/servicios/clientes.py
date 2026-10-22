from django.utils import timezone

from datos.models import Cliente
from datos.repositorios import citas as repo_citas
from datos.repositorios import clientes as repo_clientes
from datos.repositorios import clinica as repo_clinica
from datos.repositorios import reportes as repo_reportes
from datos.repositorios import ventas as repo_ventas
from negocio.excepciones import RecursoNoEncontrado, ReglaNegocioError


def buscar(busqueda="", estado="activos"):
    return repo_clientes.listar(busqueda, estado)


def pacientes_activos():
    return repo_clientes.listar_activos()


def obtener(id_cliente):
    try:
        return repo_clientes.obtener(id_cliente)
    except Cliente.DoesNotExist:
        raise RecursoNoEncontrado("El cliente no existe.")


def _validar_dpi(datos, excluir_id=None):
    dpi = datos.get("dpi")
    if dpi and repo_clientes.dpi_en_uso(dpi, excluir_id):
        raise ReglaNegocioError("Ya existe un cliente con ese DPI.", campo="dpi")


def registrar(datos):
    """Registra un cliente nuevo como activo con la fecha actual."""
    _validar_dpi(datos)
    return repo_clientes.crear(
        **datos,
        activo=True,
        fecha_registro=timezone.now(),
    )


def actualizar(id_cliente, datos):
    obtener(id_cliente)
    _validar_dpi(datos, excluir_id=id_cliente)
    repo_clientes.actualizar(id_cliente, **datos)


def cambiar_activo(id_cliente):
    cliente = obtener(id_cliente)
    repo_clientes.actualizar(id_cliente, activo=not cliente.activo)
    return not cliente.activo


def ficha(id_cliente):
    """Toda la información del cliente para su página de detalle."""
    cliente = obtener(id_cliente)
    recetas = repo_clinica.mapa_recetas_por_examen()
    examenes = [
        (examen, recetas.get(examen.id_examen))
        for examen in repo_clinica.examenes_por_cliente(id_cliente)
    ]

    return {
        "cliente": cliente,
        "resumen": repo_reportes.historial_cliente(id_cliente),
        "citas": repo_citas.por_cliente(id_cliente)[:10],
        "examenes": examenes,
        "ventas": repo_ventas.por_cliente(id_cliente)[:10],
    }
