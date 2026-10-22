from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from negocio.excepciones import ReglaNegocioError
from negocio.servicios import citas, ventas
from presentacion.utilidades import fecha_de_query, paginar


@login_required
def lista_citas(request):
    busqueda = request.GET.get("q", "").strip()
    estado = request.GET.get("estado", "")
    fecha = fecha_de_query(request)
    pagina = paginar(request, citas.buscar(busqueda, estado, fecha))

    filas = [
        (cita, citas.acciones_disponibles(cita))
        for cita in pagina["pagina"]
    ]

    return render(request, "presentacion/citas.html", {
        **pagina,
        "filas": filas,
        "busqueda": busqueda,
        "estado": estado,
        "fecha": fecha,
        "estados": citas.ESTADOS,
    })


@login_required
def registrar_cita(request):
    if request.method == "POST":
        try:
            citas.registrar(
                request.user,
                id_cliente=request.POST.get("id_cliente", ""),
                id_tipo_cita=request.POST.get("id_tipo_cita", ""),
                fecha_txt=request.POST.get("fecha_hora_inicio", ""),
                motivo=request.POST.get("motivo", ""),
                id_optometrista=request.POST.get("id_optometrista", ""),
            )
            messages.success(request, "Cita registrada correctamente.")
            return redirect("lista_citas")

        except ReglaNegocioError as error:
            messages.error(request, error.mensaje)

    return render(request, "presentacion/cita_form.html", {
        **citas.opciones_formulario(),
        "datos": request.POST,
        "cliente_inicial": request.GET.get("cliente", ""),
    })


@login_required
@require_POST
def cobrar_cita(request, id_cita):
    try:
        venta, mensaje = ventas.cobrar_cita(request.user, id_cita)
    except ReglaNegocioError as error:
        messages.error(request, error.mensaje)
        return redirect("lista_citas")

    messages.success(request, mensaje)
    return redirect("detalle_venta", venta.id_venta)


@login_required
@require_POST
def cambiar_estado_cita(request, id_cita):
    try:
        citas.cambiar_estado(
            id_cita,
            request.POST.get("estado", ""),
            request.POST.get("motivo", ""),
        )
        messages.success(request, "Estado de la cita actualizado.")
    except ReglaNegocioError as error:
        messages.error(request, error.mensaje)

    volver = request.POST.get("volver", "")
    if url_has_allowed_host_and_scheme(volver, allowed_hosts={request.get_host()}):
        return redirect(volver)
    return redirect("lista_citas")
