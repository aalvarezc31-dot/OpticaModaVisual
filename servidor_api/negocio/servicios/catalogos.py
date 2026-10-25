"""Catálogos de inventario: categorías, marcas y proveedores."""
from datos.models import CategoriaProducto, Marca, Proveedor
from datos.repositorios import inventario as repo_inventario
from negocio import validaciones
from negocio.excepciones import RecursoNoEncontrado, ReglaNegocioError


# --- Categorías ---

def categorias():
    return repo_inventario.listar_categorias()


def obtener_categoria(id_categoria):
    try:
        return repo_inventario.obtener_categoria(id_categoria)
    except CategoriaProducto.DoesNotExist:
        raise RecursoNoEncontrado("La categoría no existe.")


def guardar_categoria(datos, id_categoria=None):
    datos = {**datos, "nombre": datos["nombre"].strip().upper()}

    if repo_inventario.categoria_nombre_en_uso(datos["nombre"], id_categoria):
        raise ReglaNegocioError("Ya existe una categoría con ese nombre.", campo="nombre")

    if id_categoria:
        obtener_categoria(id_categoria)
        repo_inventario.actualizar_categoria(id_categoria, **datos)
    else:
        repo_inventario.crear_categoria(**datos)


# --- Marcas ---

def marcas():
    return repo_inventario.listar_marcas()


def obtener_marca(id_marca):
    try:
        return repo_inventario.obtener_marca(id_marca)
    except Marca.DoesNotExist:
        raise RecursoNoEncontrado("La marca no existe.")


def guardar_marca(datos, id_marca=None):
    datos = {**datos, "nombre": datos["nombre"].strip().upper()}

    if repo_inventario.marca_nombre_en_uso(datos["nombre"], id_marca):
        raise ReglaNegocioError("Ya existe una marca con ese nombre.", campo="nombre")

    if id_marca:
        obtener_marca(id_marca)
        repo_inventario.actualizar_marca(id_marca, **datos)
    else:
        repo_inventario.crear_marca(**datos)


# --- Proveedores ---

def proveedores(busqueda="", estado="activos"):
    return repo_inventario.listar_proveedores(busqueda, estado)


def obtener_proveedor(id_proveedor):
    try:
        return repo_inventario.obtener_proveedor(id_proveedor)
    except Proveedor.DoesNotExist:
        raise RecursoNoEncontrado("El proveedor no existe.")


def guardar_proveedor(datos, id_proveedor=None):
    datos = dict(datos)
    datos["nit"] = validaciones.texto_obligatorio(datos.get("nit"), "nit", "El NIT", 15).upper()
    datos["nombre"] = validaciones.texto_obligatorio(datos.get("nombre"), "nombre", "El nombre", 120)
    datos["telefono"] = validaciones.telefono(datos.get("telefono"))
    datos["email"] = validaciones.email(datos.get("email"))

    if repo_inventario.proveedor_nit_en_uso(datos["nit"], id_proveedor):
        raise ReglaNegocioError("Ya existe un proveedor con ese NIT.", campo="nit")

    if id_proveedor:
        obtener_proveedor(id_proveedor)
        repo_inventario.actualizar_proveedor(id_proveedor, **datos)
    else:
        repo_inventario.crear_proveedor(**datos, activo=True)


def cambiar_activo_proveedor(id_proveedor):
    proveedor = obtener_proveedor(id_proveedor)
    repo_inventario.actualizar_proveedor(id_proveedor, activo=not proveedor.activo)
    return not proveedor.activo
