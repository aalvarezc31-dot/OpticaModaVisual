from django.db.models import Q

from datos.models import Cliente


def listar(busqueda="", estado="activos"):
    clientes = Cliente.objects.all().order_by("-id_cliente")

    if estado == "activos":
        clientes = clientes.filter(activo=True)
    elif estado == "inactivos":
        clientes = clientes.filter(activo=False)

    if busqueda:
        clientes = clientes.filter(
            Q(nombres__icontains=busqueda)
            | Q(apellidos__icontains=busqueda)
            | Q(nit__icontains=busqueda)
            | Q(dpi__icontains=busqueda)
            | Q(telefono__icontains=busqueda)
        )

    return clientes


def listar_por_nombre():
    return Cliente.objects.filter(activo=True).order_by("nombres", "apellidos")


def listar_activos():
    return Cliente.objects.filter(activo=True).order_by("nombres")


def obtener(id_cliente):
    return Cliente.objects.get(pk=id_cliente)


def contar():
    return Cliente.objects.filter(activo=True).count()


def mapa_por_id():
    return {c.id_cliente: c for c in Cliente.objects.all()}


def dpi_en_uso(dpi, excluir_id=None):
    clientes = Cliente.objects.filter(dpi=dpi)
    if excluir_id:
        clientes = clientes.exclude(pk=excluir_id)
    return clientes.exists()


def crear(**datos):
    cliente = Cliente(**datos)
    cliente.save(force_insert=True)
    return cliente


def actualizar(id_cliente, **datos):
    Cliente.objects.filter(pk=id_cliente).update(**datos)
