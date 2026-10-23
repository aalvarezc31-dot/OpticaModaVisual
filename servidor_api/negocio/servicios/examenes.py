from django.db import IntegrityError, transaction

from datos.models import Cita, Cliente, ExamenVisual, Usuario
from datos.repositorios import citas as repo_citas
from datos.repositorios import clientes as repo_clientes
from datos.repositorios import clinica as repo_clinica
from datos.repositorios import usuarios as repo_usuarios
from negocio.excepciones import RecursoNoEncontrado, ReglaNegocioError
from negocio.servicios import sesion


def _ids_clientes_que_coinciden(busqueda):
    if not busqueda:
        return None
    return list(
        repo_clientes.listar(busqueda, estado="todos").values_list("id_cliente", flat=True)
    )


def buscar_con_paciente(busqueda=""):
    """Devuelve una lista de tuplas (examen, cliente, receta)."""
    examenes = repo_clinica.listar_examenes(
        busqueda, _ids_clientes_que_coinciden(busqueda)
    )
    clientes = repo_clientes.mapa_por_id()
    recetas = repo_clinica.mapa_recetas_por_examen()

    return [
        (examen, clientes.get(examen.id_cliente), recetas.get(examen.id_examen))
        for examen in examenes
    ]


def optometristas_activos():
    return repo_usuarios.listar_activos()


def obtener(id_examen):
    try:
        return repo_clinica.obtener_examen(id_examen)
    except ExamenVisual.DoesNotExist:
        raise RecursoNoEncontrado("El examen no existe.")


def ficha(id_examen):
    examen = obtener(id_examen)
    return {
        "examen": examen,
        "cliente": repo_clientes.mapa_por_id().get(examen.id_cliente),
        "receta": repo_clinica.receta_de_examen(id_examen),
    }


def registrar(datos):
    """
    Registra un examen visual.

    Reglas: la cita (si se indica) debe ser del mismo paciente
    y no puede tener ya un examen registrado.
    """
    try:
        cliente = repo_clientes.obtener(datos["id_cliente"])
        cita = repo_citas.obtener(datos["id_cita"]) if datos.get("id_cita") else None
        optometrista = repo_usuarios.obtener_activo(datos["id_optometrista"])
    except Cliente.DoesNotExist:
        raise ReglaNegocioError("Selecciona un paciente válido.", campo="id_cliente")
    except Cita.DoesNotExist:
        raise ReglaNegocioError("La cita no existe.", campo="id_cita")
    except Usuario.DoesNotExist:
        raise ReglaNegocioError("Selecciona un optometrista válido.", campo="id_optometrista")

    if cita and cita.id_cliente != cliente.id_cliente:
        raise ReglaNegocioError(
            "La cita seleccionada no corresponde al paciente.",
            campo="id_cita"
        )

    if cita and repo_clinica.cita_tiene_examen(cita.id_cita):
        raise ReglaNegocioError(
            "Esta cita ya tiene un examen registrado.",
            campo="id_cita"
        )

    try:
        with transaction.atomic():
            return repo_clinica.crear_examen(
                id_cliente=cliente.id_cliente,
                id_cita=cita.id_cita if cita else None,
                id_optometrista=optometrista.id_usuario,
                optometrista_nombre=sesion.nombre_completo(optometrista),
                fecha_examen=datos["fecha_examen"],
                motivo_consulta=datos["motivo_consulta"],
                antecedentes=datos["antecedentes"],
                agudeza_visual_od=datos["agudeza_visual_od"],
                agudeza_visual_oi=datos["agudeza_visual_oi"],
                presion_intraocular_od=datos["presion_intraocular_od"],
                presion_intraocular_oi=datos["presion_intraocular_oi"],
                diagnostico=datos["diagnostico"],
                observaciones=datos["observaciones"],
            )
    except IntegrityError:
        raise ReglaNegocioError(
            "No se pudo registrar el examen. "
            "Verifica si la cita ya tiene un examen."
        )
