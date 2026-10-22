from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from negocio.excepciones import ReglaNegocioError
from negocio.servicios import facturas, ventas
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
        "estados": facturas.ESTADOS,
    })


@login_required
def emitir_factura(request, id_venta):
    venta = ventas.obtener(id_venta)

    if request.method == "POST":
        form = EmitirFacturaForm(request.POST)

        if form.is_valid():
            try:
                factura = facturas.emitir(request.user, id_venta, form.cleaned_data)
                messages.success(
                    request, f"Factura {factura.serie}-{factura.numero} emitida."
                )
                return redirect("detalle_factura", factura.id_factura)
            except ReglaNegocioError as error:
                mostrar_error(request, form, error)
    else:
        form = EmitirFacturaForm(initial=facturas.datos_receptor(id_venta))

    return render(request, "presentacion/form_simple.html", {
        "form": form,
        "titulo": f"Facturar venta #{venta.id_venta}",
        "icono": "fa-file-invoice-dollar",
        "volver_id": venta.id_venta,
        "volver": "detalle_venta",
        "boton": "Emitir factura",
        "ayuda": f"Total a facturar: Q {venta.total:.2f}. El IVA (12 %) se calcula automáticamente.",
    })


@login_required
def detalle_factura(request, id_factura):
    return render(request, "presentacion/factura_detalle.html", {
        **facturas.ficha(id_factura),
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
