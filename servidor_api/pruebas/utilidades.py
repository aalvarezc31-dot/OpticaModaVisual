"""Ayudas para las pruebas unitarias (sin base de datos)."""
import contextlib
from decimal import Decimal
from types import SimpleNamespace
from unittest import mock


def sin_transaccion(modulo):
    """Reemplaza transaction.atomic del módulo por un contexto vacío (no hay BD en pruebas unitarias)."""
    return mock.patch(f"{modulo}.transaction.atomic", lambda *a, **k: contextlib.nullcontext())


def registro(**campos):
    """Objeto simple que imita un registro del ORM."""
    return SimpleNamespace(**campos)


def usuario_web(superusuario=False):
    return SimpleNamespace(is_authenticated=True, is_superuser=superusuario,
                           get_username=lambda: "prueba")


def producto(**extra):
    datos = dict(id_producto=10, codigo="MO-001", nombre="Montura", es_servicio=False,
                 activo=True, stock_actual=5, precio_venta=Decimal("250.00"),
                 precio_costo=Decimal("100.00"))
    datos.update(extra)
    return registro(**datos)


def venta(**extra):
    datos = dict(id_venta=1, estado="PENDIENTE", subtotal=Decimal("0"), descuento=Decimal("0"),
                 total=Decimal("0"), observaciones=None, id_receta=None)
    datos.update(extra)
    return registro(**datos)
