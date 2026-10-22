"""Catálogos de inventario y movimientos de stock."""
from django.db.models import Q

from datos.models import CategoriaProducto, Marca, MovimientoInventario, Proveedor

ENTRADA = "ENTRADA"
SALIDA = "SALIDA"
AJUSTE = "AJUSTE"


# --- Categorías ---

def listar_categorias():
    return CategoriaProducto.objects.all().order_by("nombre")


def obtener_categoria(id_categoria):
    return CategoriaProducto.objects.get(pk=id_categoria)


def categoria_nombre_en_uso(nombre, excluir_id=None):
    qs = CategoriaProducto.objects.filter(nombre__iexact=nombre)
    if excluir_id:
        qs = qs.exclude(pk=excluir_id)
    return qs.exists()


def crear_categoria(**datos):
    return CategoriaProducto.objects.create(**datos)


def actualizar_categoria(id_categoria, **datos):
    CategoriaProducto.objects.filter(pk=id_categoria).update(**datos)


# --- Marcas ---

def listar_marcas():
    return Marca.objects.all().order_by("nombre")


def obtener_marca(id_marca):
    return Marca.objects.get(pk=id_marca)


def marca_nombre_en_uso(nombre, excluir_id=None):
    qs = Marca.objects.filter(nombre__iexact=nombre)
    if excluir_id:
        qs = qs.exclude(pk=excluir_id)
    return qs.exists()


def crear_marca(**datos):
    return Marca.objects.create(**datos)


def actualizar_marca(id_marca, **datos):
    Marca.objects.filter(pk=id_marca).update(**datos)


# --- Proveedores ---

def listar_proveedores(busqueda="", estado="activos"):
    proveedores = Proveedor.objects.all().order_by("nombre")

    if estado == "activos":
        proveedores = proveedores.filter(activo=True)
    elif estado == "inactivos":
        proveedores = proveedores.filter(activo=False)

    if busqueda:
        proveedores = proveedores.filter(
            Q(nombre__icontains=busqueda)
            | Q(nit__icontains=busqueda)
            | Q(contacto__icontains=busqueda)
        )

    return proveedores


def obtener_proveedor(id_proveedor):
    return Proveedor.objects.get(pk=id_proveedor)


def proveedor_nit_en_uso(nit, excluir_id=None):
    qs = Proveedor.objects.filter(nit=nit)
    if excluir_id:
        qs = qs.exclude(pk=excluir_id)
    return qs.exists()


def crear_proveedor(**datos):
    return Proveedor.objects.create(**datos)


def actualizar_proveedor(id_proveedor, **datos):
    Proveedor.objects.filter(pk=id_proveedor).update(**datos)


# --- Movimientos ---

def crear_movimiento(**datos):
    """El trigger trg_movimiento_ai actualiza el stock y valida que no quede negativo."""
    return MovimientoInventario.objects.create(**datos)


def movimientos_de_producto(id_producto, limite=50):
    return MovimientoInventario.objects.filter(
        id_producto=id_producto
    ).order_by("-fecha", "-id_movimiento")[:limite]


def listar_movimientos(tipo="", limite=200):
    movimientos = MovimientoInventario.objects.all().order_by("-fecha", "-id_movimiento")
    if tipo:
        movimientos = movimientos.filter(tipo=tipo)
    return movimientos[:limite]


def existe_movimiento_de_venta(id_venta, id_producto, tipo):
    return MovimientoInventario.objects.filter(
        id_venta=id_venta, id_producto=id_producto, tipo=tipo
    ).exists()
