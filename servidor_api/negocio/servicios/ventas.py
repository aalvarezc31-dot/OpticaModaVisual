"""
Ventas.

Flujo (lo exige el trigger ventas.trg_venta_au):
    PENDIENTE -> CONFIRMADA -> PAGADA -> ENTREGADA
    PENDIENTE / CONFIRMADA / PAGADA -> ANULADA

- Mientras está PENDIENTE se agregan o quitan productos.
- Al CONFIRMAR se descuenta el stock (movimiento SALIDA por producto).
- Los pagos se registran sobre una venta CONFIRMADA; al cubrir el total
  pasa automáticamente a PAGADA.
- Al ANULAR una venta confirmada se devuelve el stock (movimiento ENTRADA).
"""
from decimal import Decimal

from django.db import DatabaseError, transaction
from django.utils import timezone

from datos.models import Cita, Cliente, DetalleVenta, MetodoPago, Producto, RecetaOptica, Venta
from datos.repositorios import citas as repo_citas
from datos.repositorios import clientes as repo_clientes
from datos.repositorios import clinica as repo_clinica
from datos.repositorios import facturas as repo_facturas
from datos.repositorios import inventario as repo_inventario
from datos.repositorios import productos as repo_productos
from datos.repositorios import ventas as repo_ventas
from negocio import validaciones
from negocio.excepciones import RecursoNoEncontrado, ReglaNegocioError, desde_error_bd
from negocio.servicios import sesion

PENDIENTE = repo_ventas.PENDIENTE
CONFIRMADA = repo_ventas.CONFIRMADA
PAGADA = repo_ventas.PAGADA
ENTREGADA = repo_ventas.ENTREGADA
ANULADA = repo_ventas.ANULADA

ESTADOS = [
    (PENDIENTE, "Pendiente"),
    (CONFIRMADA, "Confirmada"),
    (PAGADA, "Pagada"),
    (ENTREGADA, "Entregada"),
    (ANULADA, "Anulada"),
]

ESTADOS_FACTURABLES = [CONFIRMADA, PAGADA, ENTREGADA]


def estados():
    return ESTADOS


def buscar(busqueda="", estado="", fecha=None):
    return repo_ventas.listar(busqueda, estado, fecha)


def obtener(id_venta):
    try:
        return repo_ventas.obtener(id_venta)
    except Venta.DoesNotExist:
        raise RecursoNoEncontrado("La venta no existe.")


def _exigir_estado(venta, *estados, accion):
    if venta.estado not in estados:
        raise ReglaNegocioError(
            f"No se puede {accion} una venta en estado {venta.estado}."
        )


# --- Crear ---

def opciones_nueva_venta():
    clientes = repo_clientes.mapa_por_id()
    examenes = {}
    recetas = []

    for receta in repo_clinica.mapa_recetas_por_examen().values():
        examen = examenes.setdefault(
            receta.id_examen, repo_clinica.obtener_examen(receta.id_examen)
        )
        cliente = clientes.get(examen.id_cliente)
        if cliente and cliente.activo:
            recetas.append((receta, cliente))

    recetas.sort(key=lambda r: r[0].fecha_emision, reverse=True)

    return {
        "clientes": repo_clientes.listar_por_nombre(),
        "recetas": recetas,
    }


def crear(user, datos):
    agente = sesion.usuario_actual(user)

    try:
        cliente = repo_clientes.obtener(datos["id_cliente"])
    except Cliente.DoesNotExist:
        raise ReglaNegocioError("Selecciona un cliente válido.", campo="id_cliente")

    if not cliente.activo:
        raise ReglaNegocioError("El cliente está inactivo.", campo="id_cliente")

    id_receta = datos.get("id_receta")
    if id_receta:
        try:
            receta = repo_clinica.obtener_receta(id_receta)
            examen = repo_clinica.obtener_examen(receta.id_examen)
        except RecetaOptica.DoesNotExist:
            raise ReglaNegocioError("La receta no existe.", campo="id_receta")

        if examen.id_cliente != cliente.id_cliente:
            raise ReglaNegocioError(
                "La receta seleccionada es de otro paciente.", campo="id_receta"
            )

    return repo_ventas.crear(
        id_cliente=cliente.id_cliente,
        cliente_nombre=f"{cliente.nombres} {cliente.apellidos}",
        cliente_nit=cliente.nit or "CF",
        cliente_direccion=cliente.direccion or None,
        id_vendedor=agente.id_usuario,          # columna de la BD: agente que vende
        vendedor_nombre=sesion.nombre_completo(agente),
        id_receta=id_receta or None,
        fecha_venta=timezone.now(),
        subtotal=Decimal("0"),
        descuento=Decimal("0"),
        estado=PENDIENTE,
        fecha_entrega_estimada=datos.get("fecha_entrega_estimada"),
        observaciones=(datos.get("observaciones") or "").strip() or None,
    )


# --- Detalle de la venta ---

def desglose(lineas, descuento_general):
    """
    Importes de una venta o factura: bruto (cantidad x precio), descuentos por
    línea, descuento general y total. Cada `linea` necesita cantidad,
    precio_unitario y descuento.
    """
    bruto = sum((l.cantidad * l.precio_unitario for l in lineas), Decimal("0"))
    descuento_lineas = sum((l.descuento for l in lineas), Decimal("0"))
    descuento_general = descuento_general or Decimal("0")
    return {
        "bruto": bruto,
        "descuento_lineas": descuento_lineas,
        "descuento_general": descuento_general,
        "descuento_total": descuento_lineas + descuento_general,
        "total": bruto - descuento_lineas - descuento_general,
    }


def ficha(id_venta):
    venta = obtener(id_venta)
    metodos = repo_ventas.mapa_metodos()
    pagos = [
        (pago, metodos.get(pago.id_metodo_pago))
        for pago in repo_ventas.pagos(id_venta)
    ]
    pagado = repo_ventas.total_pagado(id_venta)
    factura = repo_facturas.de_venta(id_venta)
    receta = repo_clinica.obtener_receta(venta.id_receta) if venta.id_receta else None
    lineas = list(repo_ventas.lineas(id_venta))

    return {
        "venta": venta,
        "lineas": lineas,
        "desglose": desglose(lineas, venta.descuento),
        "pagos": pagos,
        "pagado": pagado,
        "saldo": (venta.total or 0) - pagado,
        "factura": factura,
        "receta": receta,
        "puede_editar": venta.estado == PENDIENTE,
        "puede_confirmar": venta.estado == PENDIENTE,
        "puede_pagar": venta.estado == CONFIRMADA,
        "puede_entregar": venta.estado == PAGADA,
        "puede_anular": venta.estado in (PENDIENTE, CONFIRMADA, PAGADA),
        "puede_facturar": venta.estado in ESTADOS_FACTURABLES and factura is None,
    }


def crear_con_productos(user, datos, lineas, descuento=Decimal("0"), confirmar_al_crear=False):
    """
    Flujo de venta en dos pasos: el carrito (`lineas`) se arma primero y
    luego se crea la venta con todo en UNA transacción: si una línea no
    cumple una regla, no queda nada guardado.

    Cada línea: {"id_producto", "cantidad", "descuento", "precio_unitario"}.
    """
    if not lineas:
        raise ReglaNegocioError("Agrega al menos un producto o servicio antes de crear la venta.",
                                campo="lineas")

    with transaction.atomic():
        venta = crear(user, datos)
        for linea in lineas:
            agregar_producto(
                venta.id_venta,
                linea["id_producto"],
                linea["cantidad"],
                linea.get("descuento") or Decimal("0"),
                linea.get("precio_unitario"),
            )
        if descuento:
            aplicar_descuento(venta.id_venta, descuento)
        if confirmar_al_crear:
            confirmar(user, venta.id_venta)

    return obtener(venta.id_venta)


def agregar_producto(id_venta, id_producto, cantidad, descuento=Decimal("0"),
                     precio_unitario=None):
    """
    Agrega un producto o servicio a una venta PENDIENTE.

    Los productos se venden a su precio de lista. Los servicios (consultas,
    cirugías...) aceptan un `precio_unitario` distinto según el caso.
    """
    venta = obtener(id_venta)
    _exigir_estado(venta, PENDIENTE, accion="modificar")

    try:
        producto = repo_productos.obtener(id_producto)
    except Producto.DoesNotExist:
        raise ReglaNegocioError("Selecciona un producto válido.", campo="id_producto")

    if not producto.activo:
        raise ReglaNegocioError("El producto está inactivo.", campo="id_producto")

    if precio_unitario is None:
        precio = producto.precio_venta
    elif producto.es_servicio:
        precio = precio_unitario
    else:
        raise ReglaNegocioError(
            "Solo los servicios permiten cambiar el precio. "
            "Para un producto usa el campo de descuento.",
            campo="precio_unitario",
        )

    existente = repo_ventas.linea_de_producto(id_venta, id_producto)

    if existente and existente.precio_unitario != precio:
        raise ReglaNegocioError(
            f"Este servicio ya está en la venta a Q {existente.precio_unitario:.2f}. "
            "Quítalo y vuelve a agregarlo con el nuevo precio.",
            campo="precio_unitario",
        )

    cantidad_total = cantidad + (existente.cantidad if existente else 0)
    descuento_total = descuento + (existente.descuento if existente else 0)

    if not producto.es_servicio and cantidad_total > producto.stock_actual:
        raise ReglaNegocioError(
            f"Stock insuficiente: hay {producto.stock_actual} disponibles.",
            campo="cantidad",
        )

    if descuento_total > cantidad_total * precio:
        raise ReglaNegocioError(
            "El descuento no puede ser mayor que el importe del producto.",
            campo="descuento",
        )

    try:
        with transaction.atomic():
            if existente:
                repo_ventas.actualizar_linea(
                    existente.id_detalle,
                    cantidad=cantidad_total,
                    descuento=descuento_total,
                )
            else:
                repo_ventas.crear_linea(
                    id_venta=id_venta,
                    id_producto=producto.id_producto,
                    producto_codigo=producto.codigo,
                    producto_nombre=producto.nombre,
                    es_servicio=producto.es_servicio,
                    cantidad=cantidad,
                    precio_unitario=precio,
                    descuento=descuento,
                )
    except DatabaseError as error:
        raise desde_error_bd(error, "No se pudo agregar el producto.")


def quitar_linea(id_venta, id_detalle):
    venta = obtener(id_venta)
    _exigir_estado(venta, PENDIENTE, accion="modificar")

    try:
        linea = repo_ventas.obtener_linea(id_detalle)
    except DetalleVenta.DoesNotExist:
        raise RecursoNoEncontrado("La línea no existe.")

    if linea.id_venta != venta.id_venta:
        raise ReglaNegocioError("La línea no pertenece a esta venta.")

    nuevo_subtotal = venta.subtotal - linea.subtotal

    try:
        with transaction.atomic():
            # El descuento general no puede quedar mayor que el nuevo subtotal.
            if venta.descuento > nuevo_subtotal:
                repo_ventas.actualizar(id_venta, descuento=max(nuevo_subtotal, 0))
            repo_ventas.eliminar_linea(id_detalle)
    except DatabaseError as error:
        raise desde_error_bd(error, "No se pudo quitar el producto.")


def aplicar_descuento(id_venta, descuento):
    venta = obtener(id_venta)
    _exigir_estado(venta, PENDIENTE, accion="modificar")

    if descuento < 0 or descuento > venta.subtotal:
        raise ReglaNegocioError(
            f"El descuento debe estar entre Q 0.00 y Q {venta.subtotal:.2f}.",
            campo="descuento",
        )

    repo_ventas.actualizar(id_venta, descuento=descuento)


# --- Cambios de estado ---

def confirmar(user, id_venta):
    venta = obtener(id_venta)
    _exigir_estado(venta, PENDIENTE, accion="confirmar")
    usuario = sesion.usuario_actual(user)
    lineas = list(repo_ventas.lineas(id_venta))

    if not lineas:
        raise ReglaNegocioError("Agrega al menos un producto antes de confirmar.")

    try:
        with transaction.atomic():
            for linea in lineas:
                if linea.es_servicio:
                    continue
                repo_inventario.crear_movimiento(
                    id_producto=linea.id_producto,
                    id_proveedor=None,
                    id_usuario=usuario.id_usuario,
                    id_venta=id_venta,
                    tipo=repo_inventario.SALIDA,
                    cantidad=linea.cantidad,
                    costo_unitario=None,
                    motivo=f"Venta #{id_venta}",
                    fecha=timezone.now(),
                )
            repo_ventas.actualizar(id_venta, estado=CONFIRMADA)
    except DatabaseError as error:
        raise desde_error_bd(error, "No se pudo confirmar la venta.")


def registrar_pago(user, id_venta, id_metodo_pago, monto, referencia=""):
    venta = obtener(id_venta)
    _exigir_estado(venta, CONFIRMADA, accion="cobrar")
    usuario = sesion.usuario_actual(user)

    try:
        repo_ventas.obtener_metodo(id_metodo_pago)
    except MetodoPago.DoesNotExist:
        raise ReglaNegocioError("Selecciona un método de pago válido.", campo="id_metodo_pago")

    saldo = venta.total - repo_ventas.total_pagado(id_venta)

    if monto <= 0:
        raise ReglaNegocioError("El monto debe ser mayor que cero.", campo="monto")

    if monto > saldo:
        raise ReglaNegocioError(
            f"El monto supera el saldo pendiente (Q {saldo:.2f}).", campo="monto"
        )

    referencia = validaciones.voucher(referencia)

    try:
        with transaction.atomic():
            repo_ventas.crear_pago(
                id_venta=id_venta,
                id_metodo_pago=id_metodo_pago,
                monto=monto,
                referencia=referencia,
                id_usuario=usuario.id_usuario,
                fecha_pago=timezone.now(),
            )
            if monto == saldo:
                repo_ventas.actualizar(id_venta, estado=PAGADA)
    except DatabaseError as error:
        raise desde_error_bd(error, "No se pudo registrar el pago.")

    return monto == saldo


def entregar(id_venta):
    venta = obtener(id_venta)
    _exigir_estado(venta, PAGADA, accion="entregar")
    repo_ventas.actualizar(id_venta, estado=ENTREGADA)


def anular(user, id_venta, motivo):
    """Anula la venta y devuelve el stock si ya se había descontado."""
    venta = obtener(id_venta)
    _exigir_estado(venta, PENDIENTE, CONFIRMADA, PAGADA, accion="anular")
    motivo = (motivo or "").strip()

    if not motivo:
        raise ReglaNegocioError("Indica el motivo de la anulación.", campo="motivo")

    factura = repo_facturas.de_venta(id_venta)
    if factura and factura.estado == repo_facturas.EMITIDA:
        raise ReglaNegocioError(
            f"Primero anula la factura {factura.serie}-{factura.numero}."
        )

    usuario = sesion.usuario_actual(user)
    observaciones = " | ".join(
        texto for texto in [venta.observaciones, f"ANULADA: {motivo}"] if texto
    )[:255]

    try:
        with transaction.atomic():
            if venta.estado in (CONFIRMADA, PAGADA):
                for linea in repo_ventas.lineas(id_venta):
                    if linea.es_servicio:
                        continue
                    repo_inventario.crear_movimiento(
                        id_producto=linea.id_producto,
                        id_proveedor=None,
                        id_usuario=usuario.id_usuario,
                        id_venta=id_venta,
                        tipo=repo_inventario.ENTRADA,
                        cantidad=linea.cantidad,
                        costo_unitario=None,
                        motivo=f"Anulación venta #{id_venta}",
                        fecha=timezone.now(),
                    )
            repo_ventas.actualizar(id_venta, estado=ANULADA, observaciones=observaciones)
    except DatabaseError as error:
        raise desde_error_bd(error, "No se pudo anular la venta.")

    return repo_ventas.total_pagado(id_venta)


# --- Cobro de una cita ---

# Servicio que se cobra según el tipo de cita (nombre del tipo -> código de producto).
SERVICIO_POR_TIPO_CITA = {
    "EXAMEN VISUAL": "SV-001",
    "CONTROL / SEGUIMIENTO": "SV-003",
    "ADAPTACION LENTES DE CONTACTO": "SV-004",
    "AJUSTE DE MONTURA": "SV-008",
}

ESTADOS_CITA_NO_COBRABLES = ["CANCELADA", "NO_ASISTIO"]


def cobrar_cita(user, id_cita):
    """
    Crea (o reutiliza) la venta de una cita con el servicio que le corresponde.

    Devuelve (venta, mensaje). La venta queda PENDIENTE para que se pueda
    ajustar el precio o agregar productos antes de confirmarla y cobrarla.
    """
    try:
        cita = repo_citas.obtener(id_cita)
    except Cita.DoesNotExist:
        raise RecursoNoEncontrado("La cita no existe.")

    if cita.estado.upper() in ESTADOS_CITA_NO_COBRABLES:
        raise ReglaNegocioError(f"No se cobra una cita en estado {cita.estado.upper()}.")

    existente = repo_ventas.de_cita(id_cita)
    if existente:
        return existente, f"Esta cita ya tiene la venta #{existente.id_venta}."

    tipo = repo_citas.mapa_tipos().get(cita.id_tipo_cita)
    nombre_tipo = tipo.nombre if tipo else "Cita"

    with transaction.atomic():
        venta = crear(user, {
            "id_cliente": cita.id_cliente,
            "observaciones": f"Cita #{id_cita} · {nombre_tipo}",
        })

        codigo = SERVICIO_POR_TIPO_CITA.get(nombre_tipo.upper())
        servicio = repo_productos.obtener_activo_por_codigo(codigo) if codigo else None

        if servicio:
            agregar_producto(venta.id_venta, servicio.id_producto, 1)
            mensaje = (f"Venta #{venta.id_venta} creada con «{servicio.nombre}». "
                       "Ajusta el precio si hace falta, confirma y registra el pago.")
        else:
            mensaje = (f"Venta #{venta.id_venta} creada. El tipo de cita «{nombre_tipo}» "
                       "no tiene servicio asignado: agrega lo que corresponda.")

    return venta, mensaje


def productos_para_venta():
    """Productos y servicios activos que se pueden agregar a una venta."""
    return repo_productos.listar_para_venta()


# --- Formulario de pago ---

def metodos_de_pago():
    return repo_ventas.listar_metodos_activos()
