"""
Facturación.

Una venta CONFIRMADA, PAGADA o ENTREGADA puede facturarse una sola vez
(uq_factura_venta). El número sale de la secuencia de la BD y el IVA lo
calcula la columna monto_iva.
"""
from decimal import ROUND_HALF_UP, Decimal

from django.db import DatabaseError, transaction
from django.utils import timezone

from datos.models import Factura
from datos.repositorios import facturas as repo_facturas
from datos.repositorios import ventas as repo_ventas
from negocio.excepciones import RecursoNoEncontrado, ReglaNegocioError, desde_error_bd
from negocio.servicios import sesion, ventas

SERIE = "A"
EMITIDA = repo_facturas.EMITIDA
ANULADA = repo_facturas.ANULADA

ESTADOS = [(EMITIDA, "Emitida"), (ANULADA, "Anulada")]

CENTAVO = Decimal("0.01")


def estados():
    return ESTADOS


def buscar(busqueda="", estado=""):
    return repo_facturas.listar(busqueda, estado)


def obtener(id_factura):
    try:
        return repo_facturas.obtener(id_factura)
    except Factura.DoesNotExist:
        raise RecursoNoEncontrado("La factura no existe.")


def ficha(id_factura):
    factura = obtener(id_factura)
    return {
        "factura": factura,
        "lineas": repo_facturas.lineas(id_factura),
        "venta": ventas.obtener(factura.id_venta),
    }


def datos_receptor(id_venta):
    """Valores iniciales del formulario de emisión."""
    venta = ventas.obtener(id_venta)
    return {
        "nit_receptor": venta.cliente_nit or "CF",
        "nombre_receptor": venta.cliente_nombre,
        "direccion_receptor": venta.cliente_direccion or "Ciudad",
    }


def _prorratear(descuento_global, lineas):
    """
    Reparte el descuento general de la venta entre las líneas para que la
    suma de la factura coincida con el total de la venta.
    """
    subtotal = sum((linea.subtotal for linea in lineas), Decimal("0"))
    repartos = []
    restante = descuento_global

    for indice, linea in enumerate(lineas):
        if indice == len(lineas) - 1 or not subtotal:
            parte = restante
        else:
            parte = (descuento_global * linea.subtotal / subtotal).quantize(
                CENTAVO, rounding=ROUND_HALF_UP
            )
        restante -= parte
        repartos.append(parte)

    return repartos


def emitir(user, id_venta, datos):
    venta = ventas.obtener(id_venta)

    if venta.estado not in ventas.ESTADOS_FACTURABLES:
        raise ReglaNegocioError(
            "Solo se facturan ventas confirmadas, pagadas o entregadas."
        )

    if repo_facturas.de_venta(id_venta):
        raise ReglaNegocioError("Esta venta ya tiene una factura.")

    usuario = sesion.usuario_actual(user)
    lineas = list(repo_ventas.lineas(id_venta))
    repartos = _prorratear(venta.descuento, lineas)

    try:
        with transaction.atomic():
            factura = repo_facturas.crear(
                id_venta=id_venta,
                serie=SERIE,
                numero=repo_facturas.siguiente_numero(),
                nit_receptor=(datos["nit_receptor"] or "CF").strip().upper(),
                nombre_receptor=datos["nombre_receptor"].strip(),
                direccion_receptor=(datos.get("direccion_receptor") or "Ciudad").strip(),
                id_usuario_emite=usuario.id_usuario,
                total=venta.total,
                estado=EMITIDA,
                fecha_emision=timezone.now(),
                fecha_anulacion=None,
                motivo_anulacion=None,
            )
            for numero, (linea, parte) in enumerate(zip(lineas, repartos), start=1):
                repo_facturas.crear_linea(
                    id_factura=factura.id_factura,
                    linea=numero,
                    descripcion=f"{linea.producto_codigo} - {linea.producto_nombre}"[:200],
                    cantidad=linea.cantidad,
                    precio_unitario=linea.precio_unitario,
                    descuento=linea.descuento + parte,
                )
    except DatabaseError as error:
        raise desde_error_bd(error, "No se pudo emitir la factura.")

    return factura


def anular(id_factura, motivo):
    factura = obtener(id_factura)
    motivo = (motivo or "").strip()

    if factura.estado != EMITIDA:
        raise ReglaNegocioError("La factura ya está anulada.")

    if not motivo:
        raise ReglaNegocioError("Indica el motivo de la anulación.", campo="motivo")

    repo_facturas.actualizar(
        id_factura,
        estado=ANULADA,
        fecha_anulacion=timezone.now(),
        motivo_anulacion=motivo[:255],
    )
