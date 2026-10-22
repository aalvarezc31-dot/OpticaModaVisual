from django.db.models import Q

from datos.models import ExamenVisual, RecetaOptica


# --- Examenes visuales ---

def listar_examenes(busqueda="", ids_clientes=None):
    examenes = ExamenVisual.objects.all().order_by("-fecha_examen")

    if busqueda:
        filtro = (
            Q(optometrista_nombre__icontains=busqueda)
            | Q(motivo_consulta__icontains=busqueda)
            | Q(diagnostico__icontains=busqueda)
        )
        if ids_clientes:
            filtro |= Q(id_cliente__in=ids_clientes)
        examenes = examenes.filter(filtro)

    return examenes


def examenes_por_cliente(id_cliente):
    return ExamenVisual.objects.filter(id_cliente=id_cliente).order_by("-fecha_examen")


def obtener_examen(id_examen):
    return ExamenVisual.objects.get(pk=id_examen)


def cita_tiene_examen(id_cita):
    return ExamenVisual.objects.filter(id_cita=id_cita).exists()


def crear_examen(**datos):
    return ExamenVisual.objects.create(**datos)


# --- Recetas opticas ---

def mapa_recetas_por_examen():
    return {r.id_examen: r for r in RecetaOptica.objects.all()}


def receta_de_examen(id_examen):
    return RecetaOptica.objects.filter(id_examen=id_examen).first()


def obtener_receta(id_receta):
    return RecetaOptica.objects.get(pk=id_receta)


def recetas_por_cliente(id_cliente):
    ids = ExamenVisual.objects.filter(id_cliente=id_cliente).values("id_examen")
    return RecetaOptica.objects.filter(id_examen__in=ids).order_by("-fecha_emision")


def examen_tiene_receta(id_examen):
    return RecetaOptica.objects.filter(id_examen=id_examen).exists()


def crear_receta(**datos):
    return RecetaOptica.objects.create(**datos)
