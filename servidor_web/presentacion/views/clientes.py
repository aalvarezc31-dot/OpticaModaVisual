from django.contrib import messages
from presentacion.sesion import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from presentacion.cliente_api import ReglaNegocioError
from presentacion.servicios import clientes
from presentacion.forms import ClienteForm
from presentacion.utilidades import mostrar_error, paginar


@login_required
def lista_clientes(request):
    busqueda = request.GET.get("q", "").strip()
    estado = request.GET.get("estado", "activos")

    return render(request, "presentacion/clientes.html", {
        **paginar(request, clientes.buscar(busqueda, estado)),
        "busqueda": busqueda,
        "estado": estado,
    })


@login_required
def registrar_cliente(request):
    if request.method == "POST":
        form = ClienteForm(request.POST)

        if form.is_valid():
            try:
                cliente = clientes.registrar(form.cleaned_data)
                messages.success(request, "Cliente registrado correctamente.")
                return redirect("detalle_cliente", cliente.id_cliente)
            except ReglaNegocioError as error:
                mostrar_error(request, form, error)
    else:
        form = ClienteForm()

    return render(request, "presentacion/cliente_form.html", {
        "form": form,
    })


@login_required
def editar_cliente(request, id_cliente):
    cliente = clientes.obtener(id_cliente)

    if request.method == "POST":
        form = ClienteForm(request.POST)

        if form.is_valid():
            try:
                clientes.actualizar(id_cliente, form.cleaned_data)
                messages.success(request, "Datos del cliente actualizados.")
                return redirect("detalle_cliente", id_cliente)
            except ReglaNegocioError as error:
                mostrar_error(request, form, error)
    else:
        form = ClienteForm(initial=cliente)

    return render(request, "presentacion/cliente_form.html", {
        "form": form,
        "cliente": cliente,
    })


@login_required
def detalle_cliente(request, id_cliente):
    return render(request, "presentacion/cliente_detalle.html", clientes.ficha(id_cliente))


@login_required
@require_POST
def cambiar_activo_cliente(request, id_cliente):
    activo = clientes.cambiar_activo(id_cliente)
    messages.success(
        request, "Cliente reactivado." if activo else "Cliente desactivado."
    )
    return redirect("detalle_cliente", id_cliente)
