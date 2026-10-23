from django.db import connection
from django.db.models import Q

from datos.models import Factura, FacturaDetalle

EMITIDA = "EMITIDA"
ANULADA = "ANULADA"


def listar(busqueda="", estado=""):
    facturas = Factura.objects.all().order_by("-fecha_emision", "-id_factura")

    if estado:
        facturas = facturas.filter(estado=estado)

    if busqueda:
        filtro = (
            Q(nombre_receptor__icontains=busqueda)
            | Q(nit_receptor__icontains=busqueda)
        )
        if busqueda.isdigit():
            filtro |= Q(numero=int(busqueda)) | Q(id_venta=int(busqueda))
        facturas = facturas.filter(filtro)

    return facturas


def obtener(id_factura):
    return Factura.objects.get(pk=id_factura)


def de_venta(id_venta):
    return Factura.objects.filter(id_venta=id_venta).first()


def siguiente_numero():
    """Toma el siguiente valor de la secuencia facturacion.seq_numero_factura."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT NEXT VALUE FOR facturacion.seq_numero_factura")
        return cursor.fetchone()[0]


def crear(**datos):
    return Factura.objects.create(**datos)


def actualizar(id_factura, **datos):
    Factura.objects.filter(pk=id_factura).update(**datos)


def lineas(id_factura):
    return FacturaDetalle.objects.filter(id_factura=id_factura).order_by("linea")


def crear_linea(**datos):
    return FacturaDetalle.objects.create(**datos)
