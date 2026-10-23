from django.db.models import Q, Sum

from datos.models import DetalleVenta, MetodoPago, Pago, Venta

# Valores permitidos por ck_venta_estado.
PENDIENTE = "PENDIENTE"
CONFIRMADA = "CONFIRMADA"
PAGADA = "PAGADA"
ENTREGADA = "ENTREGADA"
ANULADA = "ANULADA"


def listar(busqueda="", estado="", fecha=None):
    ventas = Venta.objects.all().order_by("-fecha_venta", "-id_venta")

    if estado:
        ventas = ventas.filter(estado=estado)

    if fecha:
        ventas = ventas.filter(fecha_venta__date=fecha)

    if busqueda:
        filtro = (
            Q(cliente_nombre__icontains=busqueda)
            | Q(cliente_nit__icontains=busqueda)
            | Q(vendedor_nombre__icontains=busqueda)
        )
        if busqueda.isdigit():
            filtro |= Q(id_venta=int(busqueda))
        ventas = ventas.filter(filtro)

    return ventas


def por_cliente(id_cliente):
    return Venta.objects.filter(id_cliente=id_cliente).order_by("-fecha_venta")


def obtener(id_venta):
    return Venta.objects.get(pk=id_venta)


def crear(**datos):
    return Venta.objects.create(**datos)


def de_cita(id_cita):
    """Venta no anulada que se generó al cobrar la cita (ver MARCA_CITA en negocio)."""
    return Venta.objects.filter(
        observaciones__startswith=f"Cita #{id_cita} "
    ).exclude(estado=ANULADA).first()


def actualizar(id_venta, **datos):
    """
    Actualiza solo las columnas indicadas.

    Nunca se usa venta.save(): sobrescribiría el subtotal que
    mantiene el trigger trg_detalle_venta_aiud.
    """
    Venta.objects.filter(pk=id_venta).update(**datos)


def total_vendido_del_dia(dia):
    return Venta.objects.filter(
        fecha_venta__date=dia
    ).exclude(
        estado__in=[PENDIENTE, ANULADA]
    ).aggregate(total=Sum("total"))["total"] or 0


def contar_por_estado(estado):
    return Venta.objects.filter(estado=estado).count()


# --- Detalle ---

def lineas(id_venta):
    return DetalleVenta.objects.filter(id_venta=id_venta).order_by("id_detalle")


def obtener_linea(id_detalle):
    return DetalleVenta.objects.get(pk=id_detalle)


def linea_de_producto(id_venta, id_producto):
    return DetalleVenta.objects.filter(id_venta=id_venta, id_producto=id_producto).first()


def crear_linea(**datos):
    return DetalleVenta.objects.create(**datos)


def actualizar_linea(id_detalle, **datos):
    DetalleVenta.objects.filter(pk=id_detalle).update(**datos)


def eliminar_linea(id_detalle):
    DetalleVenta.objects.filter(pk=id_detalle).delete()


# --- Pagos ---

def pagos(id_venta):
    return Pago.objects.filter(id_venta=id_venta).order_by("fecha_pago")


def total_pagado(id_venta):
    return Pago.objects.filter(id_venta=id_venta).aggregate(
        total=Sum("monto")
    )["total"] or 0


def crear_pago(**datos):
    return Pago.objects.create(**datos)


def listar_metodos_activos():
    return MetodoPago.objects.filter(activo=True).order_by("nombre")


def obtener_metodo(id_metodo_pago):
    return MetodoPago.objects.get(pk=id_metodo_pago, activo=True)


def mapa_metodos():
    return {m.id_metodo_pago: m for m in MetodoPago.objects.all()}
