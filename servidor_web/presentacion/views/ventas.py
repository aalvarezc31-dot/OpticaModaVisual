from django.contrib import messages
from presentacion.sesion import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from presentacion.cliente_api import ReglaNegocioError
from presentacion.servicios import ventas
from presentacion.forms import (
    DescuentoVentaForm, LineaVentaForm, MotivoForm, NuevaVentaForm, PagoForm,
)
from presentacion.utilidades import fecha_de_query, mostrar_error, paginar


@login_required
def lista_ventas(request):
    busqueda = request.GET.get("q", "").strip()
    estado = request.GET.get("estado", "")
    fecha = fecha_de_query(request)

    return render(request, "presentacion/ventas.html", {
        **paginar(request, ventas.buscar(busqueda, estado, fecha)),
        "busqueda": busqueda,
        "estado": estado,
        "fecha": fecha,
        "estados": ventas.estados(),
    })


@login_required
def nueva_venta(request):
    if request.method == "POST":
        form = NuevaVentaForm(request.POST)

        if form.is_valid():
            try:
                venta = ventas.crear(form.cleaned_data)
                messages.success(
                    request, f"Venta #{venta.id_venta} creada. Agrega los productos."
                )
                return redirect("detalle_venta", venta.id_venta)
            except ReglaNegocioError as error:
                mostrar_error(request, form, error)
    else:
        iniciales = {}
        if request.GET.get("cliente", "").isdigit():
            iniciales["id_cliente"] = int(request.GET["cliente"])
        form = NuevaVentaForm(initial=iniciales)

    return render(request, "presentacion/form_simple.html", {
        "form": form,
        "titulo": "Nueva venta",
        "icono": "fa-cart-plus",
        "volver": "lista_ventas",
        "boton": "Crear venta",
        "ayuda": "Después de crearla podrás agregar productos, confirmarla y registrar pagos.",
    })


def _render_detalle(request, id_venta, **formularios):
    contexto = ventas.ficha(id_venta)
    venta = contexto["venta"]
    form_linea = formularios.get("form_linea") or LineaVentaForm()

    return render(request, "presentacion/venta_detalle.html", {
        **contexto,
        "form_linea": form_linea,
        "servicios_precios": {
            str(id_producto): f"{precio:.2f}"
            for id_producto, precio in form_linea.servicios.items()
        },
        "form_descuento": formularios.get("form_descuento") or DescuentoVentaForm(
            initial={"descuento": venta.descuento}
        ),
        "form_pago": formularios.get("form_pago") or PagoForm(
            initial={"monto": contexto["saldo"]}
        ),
        "form_anular": formularios.get("form_anular") or MotivoForm(),
    })


@login_required
def detalle_venta(request, id_venta):
    return _render_detalle(request, id_venta)


@login_required
@require_POST
def agregar_linea(request, id_venta):
    form = LineaVentaForm(request.POST)

    if form.is_valid():
        try:
            ventas.agregar_producto(
                id_venta,
                form.cleaned_data["id_producto"],
                form.cleaned_data["cantidad"],
                form.cleaned_data["descuento"],
                form.cleaned_data["precio_unitario"],
            )
            messages.success(request, "Producto agregado.")
            return redirect("detalle_venta", id_venta)
        except ReglaNegocioError as error:
            mostrar_error(request, form, error)

    return _render_detalle(request, id_venta, form_linea=form)


@login_required
@require_POST
def quitar_linea(request, id_venta, id_detalle):
    try:
        ventas.quitar_linea(id_venta, id_detalle)
        messages.success(request, "Producto quitado de la venta.")
    except ReglaNegocioError as error:
        messages.error(request, error.mensaje)

    return redirect("detalle_venta", id_venta)


@login_required
@require_POST
def aplicar_descuento(request, id_venta):
    form = DescuentoVentaForm(request.POST)

    if form.is_valid():
        try:
            ventas.aplicar_descuento(id_venta, form.cleaned_data["descuento"])
            messages.success(request, "Descuento aplicado.")
            return redirect("detalle_venta", id_venta)
        except ReglaNegocioError as error:
            mostrar_error(request, form, error)

    return _render_detalle(request, id_venta, form_descuento=form)


@login_required
@require_POST
def confirmar_venta(request, id_venta):
    try:
        ventas.confirmar(id_venta)
        messages.success(request, "Venta confirmada. Se descontó el inventario.")
    except ReglaNegocioError as error:
        messages.error(request, error.mensaje)

    return redirect("detalle_venta", id_venta)


@login_required
@require_POST
def registrar_pago(request, id_venta):
    form = PagoForm(request.POST)

    if form.is_valid():
        try:
            pagada = ventas.registrar_pago(
                id_venta,
                form.cleaned_data["id_metodo_pago"],
                form.cleaned_data["monto"],
                form.cleaned_data["referencia"],
            )
            messages.success(
                request,
                "Pago registrado. La venta quedó PAGADA." if pagada
                else "Pago parcial registrado."
            )
            return redirect("detalle_venta", id_venta)
        except ReglaNegocioError as error:
            mostrar_error(request, form, error)

    return _render_detalle(request, id_venta, form_pago=form)


@login_required
@require_POST
def entregar_venta(request, id_venta):
    try:
        ventas.entregar(id_venta)
        messages.success(request, "Venta marcada como ENTREGADA.")
    except ReglaNegocioError as error:
        messages.error(request, error.mensaje)

    return redirect("detalle_venta", id_venta)


@login_required
@require_POST
def anular_venta(request, id_venta):
    form = MotivoForm(request.POST)

    if form.is_valid():
        try:
            pagado = ventas.anular(id_venta, form.cleaned_data["motivo"])
            mensaje = "Venta anulada."
            if pagado:
                mensaje += f" Recuerda devolver al cliente Q {pagado:.2f} ya pagados."
            messages.success(request, mensaje)
            return redirect("detalle_venta", id_venta)
        except ReglaNegocioError as error:
            mostrar_error(request, form, error)

    return _render_detalle(request, id_venta, form_anular=form)
