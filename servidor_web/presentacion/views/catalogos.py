from django.contrib import messages
from presentacion.sesion import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from presentacion.cliente_api import ReglaNegocioError
from presentacion.servicios import catalogos
from presentacion.forms import CategoriaForm, MarcaForm, ProveedorForm
from presentacion.utilidades import mostrar_error, paginar


# --- Proveedores ---

@login_required
def lista_proveedores(request):
    busqueda = request.GET.get("q", "").strip()
    estado = request.GET.get("estado", "activos")

    return render(request, "presentacion/proveedores.html", {
        **paginar(request, catalogos.proveedores(busqueda, estado)),
        "busqueda": busqueda,
        "estado": estado,
    })


@login_required
def guardar_proveedor(request, id_proveedor=None):
    proveedor = catalogos.obtener_proveedor(id_proveedor) if id_proveedor else None

    if request.method == "POST":
        form = ProveedorForm(request.POST)

        if form.is_valid():
            try:
                catalogos.guardar_proveedor(form.cleaned_data, id_proveedor)
                messages.success(request, "Proveedor guardado correctamente.")
                return redirect("lista_proveedores")
            except ReglaNegocioError as error:
                mostrar_error(request, form, error)
    else:
        form = ProveedorForm(initial=proveedor)

    return render(request, "presentacion/form_simple.html", {
        "form": form,
        "titulo": "Editar proveedor" if proveedor else "Nuevo proveedor",
        "icono": "fa-truck",
        "volver": "lista_proveedores",
    })


@login_required
@require_POST
def cambiar_activo_proveedor(request, id_proveedor):
    activo = catalogos.cambiar_activo_proveedor(id_proveedor)
    messages.success(
        request, "Proveedor reactivado." if activo else "Proveedor desactivado."
    )
    return redirect("lista_proveedores")


# --- Categorías y marcas (una sola página) ---

def _render_catalogos(request, form_categoria=None, form_marca=None,
                      categoria=None, marca=None):
    return render(request, "presentacion/catalogos.html", {
        "categorias": catalogos.categorias(),
        "marcas": catalogos.marcas(),
        "form_categoria": form_categoria or CategoriaForm(initial=categoria),
        "form_marca": form_marca or MarcaForm(initial=marca),
        "categoria_editando": categoria,
        "marca_editando": marca,
    })


@login_required
def catalogos_inventario(request):
    categoria = marca = None

    if request.GET.get("categoria"):
        categoria = catalogos.obtener_categoria(int(request.GET["categoria"]))
    if request.GET.get("marca"):
        marca = catalogos.obtener_marca(int(request.GET["marca"]))

    return _render_catalogos(request, categoria=categoria, marca=marca)


@login_required
@require_POST
def guardar_categoria(request, id_categoria=None):
    categoria = catalogos.obtener_categoria(id_categoria) if id_categoria else None
    form = CategoriaForm(request.POST)

    if form.is_valid():
        try:
            catalogos.guardar_categoria(form.cleaned_data, id_categoria)
            messages.success(request, "Categoría guardada.")
            return redirect("catalogos_inventario")
        except ReglaNegocioError as error:
            mostrar_error(request, form, error)

    return _render_catalogos(request, form_categoria=form, categoria=categoria)


@login_required
@require_POST
def guardar_marca(request, id_marca=None):
    marca = catalogos.obtener_marca(id_marca) if id_marca else None
    form = MarcaForm(request.POST)

    if form.is_valid():
        try:
            catalogos.guardar_marca(form.cleaned_data, id_marca)
            messages.success(request, "Marca guardada.")
            return redirect("catalogos_inventario")
        except ReglaNegocioError as error:
            mostrar_error(request, form, error)

    return _render_catalogos(request, form_marca=form, marca=marca)
