from django.contrib import messages
from presentacion.sesion import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from presentacion.cliente_api import ReglaNegocioError
from presentacion.servicios import facturas, ventas
from presentacion.forms import EmitirFacturaForm, MotivoForm
from presentacion.utilidades import mostrar_error, paginar


@login_required
def lista_facturas(request):
    busqueda = request.GET.get("q", "").strip()
    estado = request.GET.get("estado", "")

    return render(request, "presentacion/facturas.html", {
        **paginar(request, facturas.buscar(busqueda, estado)),
        "busqueda": busqueda,
        "estado": estado,
        "estados": facturas.estados(),
    })


@login_required
def emitir_factura(request, id_venta):
    venta = ventas.obtener(id_venta)

    if request.method == "POST":
        form = EmitirFacturaForm(request.POST)

        if form.is_valid():
            try:
                factura = facturas.emitir(id_venta, form.cleaned_data)
                messages.success(
                    request, f"Factura {factura.serie}-{factura.numero} emitida."
                )
                return redirect("detalle_factura", factura.id_factura)
            except ReglaNegocioError as error:
                mostrar_error(request, form, error)
    else:
        form = EmitirFacturaForm(initial=facturas.datos_receptor(id_venta))

    return render(request, "presentacion/factura_emitir.html", {
        "form": form,
        "venta": venta,
        "desglose": facturas.vista_previa(id_venta),
    })


@login_required
def detalle_factura(request, id_factura):
    contexto = facturas.ficha(id_factura)
    for linea in contexto["lineas"]:
        linea.importe = linea.cantidad * linea.precio_unitario
    return render(request, "presentacion/factura_detalle.html", {
        **contexto,
        "form_anular": MotivoForm(),
    })


@login_required
@require_POST
def anular_factura(request, id_factura):
    form = MotivoForm(request.POST)

    if form.is_valid():
        try:
            facturas.anular(id_factura, form.cleaned_data["motivo"])
            messages.success(request, "Factura anulada.")
        except ReglaNegocioError as error:
            messages.error(request, error.mensaje)
    else:
        messages.error(request, "Indica el motivo de la anulación.")

    return redirect("detalle_factura", id_factura)
