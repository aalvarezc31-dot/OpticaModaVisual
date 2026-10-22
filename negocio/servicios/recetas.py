from django.db import IntegrityError, transaction

from datos.models import RecetaOptica
from datos.repositorios import clientes as repo_clientes
from datos.repositorios import clinica as repo_clinica
from negocio.excepciones import RecursoNoEncontrado, ReglaNegocioError
from negocio.servicios import examenes

CAMPOS_RECETA = [
    "od_esfera", "od_cilindro", "od_eje", "od_adicion",
    "oi_esfera", "oi_cilindro", "oi_eje", "oi_adicion",
    "distancia_pupilar", "tipo_lente", "tratamiento", "indicaciones",
    "fecha_emision", "fecha_vencimiento",
]


def resultados(busqueda=""):
    """Devuelve una lista de tuplas (examen, cliente, receta)."""
    return examenes.buscar_con_paciente(busqueda)


def examen_para_receta(id_examen):
    """
    Devuelve el examen al que se le va a registrar receta.

    Lanza RecursoNoEncontrado si no existe y ReglaNegocioError
    si el examen ya tiene una receta.
    """
    examen = examenes.obtener(id_examen)

    if repo_clinica.examen_tiene_receta(examen.id_examen):
        raise ReglaNegocioError(
            "Este examen ya tiene una receta óptica registrada."
        )

    return examen


def registrar(examen, datos):
    try:
        with transaction.atomic():
            return repo_clinica.crear_receta(
                id_examen=examen.id_examen,
                **{campo: datos[campo] for campo in CAMPOS_RECETA},
            )
    except IntegrityError:
        raise ReglaNegocioError(
            "No se pudo registrar la receta. "
            "Es posible que el examen ya tenga una."
        )


def ficha(id_receta):
    """Receta con su examen y paciente, para verla o imprimirla."""
    try:
        receta = repo_clinica.obtener_receta(id_receta)
    except RecetaOptica.DoesNotExist:
        raise RecursoNoEncontrado("La receta no existe.")

    examen = repo_clinica.obtener_examen(receta.id_examen)

    return {
        "receta": receta,
        "examen": examen,
        "cliente": repo_clientes.mapa_por_id().get(examen.id_cliente),
    }
