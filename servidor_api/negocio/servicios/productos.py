from django.db import DatabaseError, transaction
from django.utils import timezone

from datos.models import Producto
from datos.repositorios import inventario as repo_inventario
from datos.repositorios import productos as repo_productos
from negocio.excepciones import RecursoNoEncontrado, ReglaNegocioError, desde_error_bd
from negocio.servicios import sesion

TIPOS_MOVIMIENTO = [
    (repo_inventario.ENTRADA, "Entrada (compra / ingreso)"),
    (repo_inventario.SALIDA, "Salida (merma / uso interno)"),
    (repo_inventario.AJUSTE, "Ajuste de inventario (+/-)"),
]


def tipos_movimiento():
    return TIPOS_MOVIMIENTO


def buscar(busqueda="", id_categoria=None, estado="activos", solo_stock_bajo=False):
    return repo_productos.listar(busqueda, id_categoria, estado, solo_stock_bajo)


def disponibles_para_venta():
    return repo_productos.listar_para_venta()


def obtener(id_producto):
    try:
        return repo_productos.obtener(id_producto)
    except Producto.DoesNotExist:
        raise RecursoNoEncontrado("El producto no existe.")


def opciones_catalogo():
    return {
        "categorias": repo_inventario.listar_categorias(),
        "marcas": repo_inventario.listar_marcas(),
        "proveedores": repo_inventario.listar_proveedores(estado="activos"),
    }


def _validar(datos, excluir_id=None):
    if repo_productos.codigo_en_uso(datos["codigo"], excluir_id):
        raise ReglaNegocioError("Ya existe un producto con ese código.", campo="codigo")

    if datos["precio_venta"] < datos["precio_costo"]:
        raise ReglaNegocioError(
            "El precio de venta no puede ser menor que el costo.",
            campo="precio_venta",
        )


def validar(datos, excluir_id=None):
    """Reglas de código único y precio; lanza ReglaNegocioError."""
    _validar(datos, excluir_id)


def registrar(user, datos):
    """
    Registra un producto activo.

    El stock inicial se carga como un movimiento de ENTRADA: en la BD el
    stock solo cambia a través de inventario.movimiento_inventario.
    """
    datos = dict(datos)
    stock_inicial = datos.pop("stock_inicial", 0) or 0
    _validar(datos)

    if datos["es_servicio"]:
        stock_inicial = 0
        datos["stock_minimo"] = 0

    usuario = sesion.usuario_actual(user) if stock_inicial else None

    try:
        with transaction.atomic():
            producto = repo_productos.crear(
                **datos,
                stock_actual=0,
                activo=True,
                fecha_creacion=timezone.now(),
            )
            if stock_inicial:
                repo_inventario.crear_movimiento(
                    id_producto=producto.id_producto,
                    id_proveedor=datos.get("id_proveedor"),
                    id_usuario=usuario.id_usuario,
                    id_venta=None,
                    tipo=repo_inventario.ENTRADA,
                    cantidad=stock_inicial,
                    costo_unitario=datos["precio_costo"],
                    motivo="Stock inicial",
                    fecha=timezone.now(),
                )
    except DatabaseError as error:
        raise desde_error_bd(error, "No se pudo registrar el producto.")

    return producto


def actualizar(id_producto, datos):
    producto = obtener(id_producto)
    datos = dict(datos)
    datos.pop("stock_inicial", None)
    _validar(datos, excluir_id=id_producto)

    if datos["es_servicio"] and producto.stock_actual:
        raise ReglaNegocioError(
            "No se puede convertir en servicio un producto con existencias.",
            campo="es_servicio",
        )

    repo_productos.actualizar(id_producto, **datos)


def cambiar_activo(id_producto):
    producto = obtener(id_producto)
    repo_productos.actualizar(id_producto, activo=not producto.activo)
    return not producto.activo


def ficha(id_producto):
    producto = obtener(id_producto)
    return {
        "producto": producto,
        "valor_inventario": producto.stock_actual * producto.precio_costo,
        "movimientos": repo_inventario.movimientos_de_producto(id_producto),
    }


def ajustar_stock(user, id_producto, nuevo_stock, motivo=""):
    """
    Deja las existencias en `nuevo_stock` registrando un movimiento de AJUSTE
    por la diferencia (en la BD el stock solo cambia con movimientos).
    Devuelve la diferencia aplicada (0 si no hubo cambio).
    """
    producto = obtener(id_producto)

    if nuevo_stock is None or nuevo_stock == producto.stock_actual:
        return 0

    if nuevo_stock < 0:
        raise ReglaNegocioError("Las existencias no pueden ser negativas.", campo="stock_nuevo")

    diferencia = nuevo_stock - producto.stock_actual
    registrar_movimiento(user, id_producto, {
        "tipo": repo_inventario.AJUSTE,
        "cantidad": diferencia,
        "costo_unitario": None,
        "motivo": (motivo or "").strip() or "Ajuste desde el panel administrativo",
    })
    return diferencia


def registrar_movimiento(user, id_producto, datos):
    """ENTRADA, SALIDA o AJUSTE manual de inventario."""
    producto = obtener(id_producto)
    tipo = datos["tipo"]
    cantidad = datos["cantidad"]

    if producto.es_servicio:
        raise ReglaNegocioError("Los servicios no manejan inventario.")

    if tipo in (repo_inventario.ENTRADA, repo_inventario.SALIDA) and cantidad <= 0:
        raise ReglaNegocioError(
            "La cantidad debe ser mayor que cero.", campo="cantidad"
        )

    if tipo == repo_inventario.AJUSTE and cantidad == 0:
        raise ReglaNegocioError(
            "El ajuste no puede ser cero. Usa negativo para restar.",
            campo="cantidad",
        )

    usuario = sesion.usuario_actual(user)

    try:
        with transaction.atomic():
            repo_inventario.crear_movimiento(
                id_producto=id_producto,
                id_proveedor=(
                    datos.get("id_proveedor")
                    if tipo == repo_inventario.ENTRADA else None
                ),
                id_usuario=usuario.id_usuario,
                id_venta=None,
                tipo=tipo,
                cantidad=cantidad,
                costo_unitario=datos.get("costo_unitario"),
                motivo=(datos.get("motivo") or "").strip() or None,
                fecha=timezone.now(),
            )
    except DatabaseError as error:
        raise desde_error_bd(error, "No se pudo registrar el movimiento.")
