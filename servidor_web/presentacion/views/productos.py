from django.contrib import messages
from presentacion.sesion import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from presentacion.cliente_api import ReglaNegocioError
from presentacion.servicios import catalogos, productos
from presentacion.forms import MovimientoForm, ProductoForm
from presentacion.utilidades import mostrar_error, paginar


@login_required
def lista_productos(request):
    busqueda = request.GET.get("q", "").strip()
    estado = request.GET.get("estado", "activos")
    stock_bajo = request.GET.get("stock_bajo") == "1"

    try:
        id_categoria = int(request.GET.get("categoria", ""))
    except ValueError:
        id_categoria = None

    registros = productos.buscar(busqueda, id_categoria, estado, stock_bajo)
    categorias = list(catalogos.categorias())
    nombres = {c.id_categoria: c.nombre for c in categorias}
    pagina = paginar(request, registros)

    for producto in pagina["pagina"]:
        producto.categoria_nombre = nombres.get(producto.id_categoria)

    return render(request, "presentacion/productos.html", {
        **pagina,
        "busqueda": busqueda,
        "estado": estado,
        "stock_bajo": stock_bajo,
        "id_categoria": id_categoria,
        "categorias": categorias,
    })


@login_required
def registrar_producto(request):
    if request.method == "POST":
        form = ProductoForm(request.POST)

        if form.is_valid():
            try:
                producto = productos.registrar(form.cleaned_data)
                messages.success(request, "Producto registrado correctamente.")
                return redirect("detalle_producto", producto.id_producto)
            except ReglaNegocioError as error:
                mostrar_error(request, form, error)
    else:
        form = ProductoForm()

    return render(request, "presentacion/producto_form.html", {
        "form": form,
    })


@login_required
def editar_producto(request, id_producto):
    producto = productos.obtener(id_producto)

    if request.method == "POST":
        form = ProductoForm(request.POST, initial=producto, nuevo=False)

        if form.is_valid():
            try:
                productos.actualizar(id_producto, form.cleaned_data)
                messages.success(request, "Producto actualizado.")
                return redirect("detalle_producto", id_producto)
            except ReglaNegocioError as error:
                mostrar_error(request, form, error)
    else:
        form = ProductoForm(initial=producto, nuevo=False)

    return render(request, "presentacion/producto_form.html", {
        "form": form,
        "producto": producto,
    })


def _render_detalle(request, id_producto, form_movimiento=None):
    contexto = productos.ficha(id_producto)
    producto = contexto["producto"]
    nombres = {c.id_categoria: c.nombre for c in catalogos.categorias()}
    marcas = {m.id_marca: m.nombre for m in catalogos.marcas()}

    return render(request, "presentacion/producto_detalle.html", {
        **contexto,
        "categoria": nombres.get(producto.id_categoria),
        "marca": marcas.get(producto.id_marca),
        "proveedor": (
            catalogos.obtener_proveedor(producto.id_proveedor)
            if producto.id_proveedor else None
        ),
        "form_movimiento": form_movimiento or MovimientoForm(
            initial={"costo_unitario": producto.precio_costo}
        ),
    })


@login_required
def detalle_producto(request, id_producto):
    return _render_detalle(request, id_producto)


@login_required
@require_POST
def registrar_movimiento(request, id_producto):
    form = MovimientoForm(request.POST)

    if form.is_valid():
        try:
            productos.registrar_movimiento(id_producto, form.cleaned_data)
            messages.success(request, "Movimiento registrado. El stock se actualizó.")
            return redirect("detalle_producto", id_producto)
        except ReglaNegocioError as error:
            mostrar_error(request, form, error)

    return _render_detalle(request, id_producto, form)


@login_required
@require_POST
def cambiar_activo_producto(request, id_producto):
    activo = productos.cambiar_activo(id_producto)
    messages.success(
        request, "Producto reactivado." if activo else "Producto desactivado."
    )
    return redirect("detalle_producto", id_producto)
