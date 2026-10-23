from django.db.models import Q

from datos.models import Cita, TipoCita

# Valores permitidos por ck_cita_estado.
PROGRAMADA = "PROGRAMADA"
CONFIRMADA = "CONFIRMADA"
ATENDIDA = "ATENDIDA"
CANCELADA = "CANCELADA"
NO_ASISTIO = "NO_ASISTIO"

# Citas que ya no ocupan horario.
ESTADOS_LIBERADOS = [CANCELADA, NO_ASISTIO]


def _vigentes():
    return Cita.objects.exclude(estado__in=ESTADOS_LIBERADOS)


def listar(busqueda="", estado="", fecha=None):
    citas = Cita.objects.all().order_by("-fecha_hora_inicio")

    if estado:
        citas = citas.filter(estado=estado)

    if fecha:
        citas = citas.filter(fecha_hora_inicio__date=fecha)

    if busqueda:
        citas = citas.filter(
            Q(cliente_nombre__icontains=busqueda)
            | Q(cliente_telefono__icontains=busqueda)
            | Q(motivo__icontains=busqueda)
            | Q(usuario_atiende_nombre__icontains=busqueda)
        )

    return citas


def listar_recientes_primero():
    return Cita.objects.all().order_by("-fecha_hora_inicio")


def por_cliente(id_cliente):
    return Cita.objects.filter(id_cliente=id_cliente).order_by("-fecha_hora_inicio")


def obtener(id_cita):
    return Cita.objects.get(pk=id_cita)


def existe_traslape(inicio, fin):
    return _vigentes().filter(
        fecha_hora_inicio__lt=fin,
        fecha_hora_fin__gt=inicio,
    ).exists()


def contar_vigentes_del_dia(dia):
    return _vigentes().filter(fecha_hora_inicio__date=dia).count()


def contar_del_dia(dia):
    return Cita.objects.filter(fecha_hora_inicio__date=dia).count()


def proximas_vigentes(desde, limite=5):
    return list(
        _vigentes().filter(
            fecha_hora_inicio__gte=desde
        ).exclude(estado=ATENDIDA).order_by("fecha_hora_inicio")[:limite]
    )


def crear(**datos):
    return Cita.objects.create(**datos)


def actualizar(id_cita, **datos):
    Cita.objects.filter(pk=id_cita).update(**datos)


# --- Tipos de cita ---

def listar_tipos_activos():
    return TipoCita.objects.filter(activo=True).order_by("nombre")


def obtener_tipo_activo(id_tipo_cita):
    return listar_tipos_activos().get(pk=id_tipo_cita)


def mapa_tipos():
    return {t.id_tipo_cita: t for t in TipoCita.objects.all()}
