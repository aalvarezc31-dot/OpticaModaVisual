"""Capa de datos: modelos ORM (uno por esquema de la base de datos)."""
from .citas import Cita, HorarioAtencion, TipoCita  # noqa: F401
from .clientes import Cliente  # noqa: F401
from .clinica import ExamenVisual, RecetaOptica  # noqa: F401
from .facturacion import Factura, FacturaDetalle  # noqa: F401
from .inventario import CategoriaProducto, Marca, MovimientoInventario, Producto, Proveedor  # noqa: F401
from .seguridad import Bitacora, RefreshToken, Rol, Usuario  # noqa: F401
from .ventas import DetalleVenta, MetodoPago, OutboxEvento, Pago, Venta  # noqa: F401
