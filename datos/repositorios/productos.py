from django.db.models import F, Q

from datos.models import Producto


def listar(busqueda="", id_categoria=None, estado="activos", solo_stock_bajo=False):
    productos = Producto.objects.all().order_by("nombre")

    if estado == "activos":
        productos = productos.filter(activo=True)
    elif estado == "inactivos":
        productos = productos.filter(activo=False)

    if id_categoria:
        productos = productos.filter(id_categoria=id_categoria)

    if solo_stock_bajo:
        productos = productos.filter(
            es_servicio=False, stock_actual__lte=F("stock_minimo")
        )

    if busqueda:
        productos = productos.filter(
            Q(codigo__icontains=busqueda)
            | Q(nombre__icontains=busqueda)
            | Q(modelo__icontains=busqueda)
            | Q(color__icontains=busqueda)
            | Q(material__icontains=busqueda)
        )

    return productos


def listar_activos(busqueda=""):
    return listar(busqueda, estado="activos")


def listar_para_venta():
    return Producto.objects.filter(activo=True).order_by("nombre")


def obtener(id_producto):
    return Producto.objects.get(pk=id_producto)


def obtener_activo_por_codigo(codigo):
    return Producto.objects.filter(codigo=codigo, activo=True).first()


def contar_activos():
    return Producto.objects.filter(activo=True).count()


def contar_stock_bajo():
    return Producto.objects.filter(
        activo=True, es_servicio=False, stock_actual__lte=F("stock_minimo")
    ).count()


def codigo_en_uso(codigo, excluir_id=None):
    productos = Producto.objects.filter(codigo=codigo)
    if excluir_id:
        productos = productos.exclude(pk=excluir_id)
    return productos.exists()


def crear(**datos):
    producto = Producto(**datos)
    producto.save(force_insert=True)
    return producto


def actualizar(id_producto, **datos):
    # Nunca incluye stock_actual: el stock solo cambia por movimientos.
    Producto.objects.filter(pk=id_producto).update(**datos)
