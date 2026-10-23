"""Modelos del esquema [facturacion]."""
from decimal import Decimal

from django.db import models
from django.db.models import F, Value
from django.db.models.functions import Round

# Columnas calculadas por SQL Server: Django nunca las escribe.
_MONEDA = models.DecimalField(max_digits=12, decimal_places=2)


class Factura(models.Model):
    id_factura = models.AutoField(primary_key=True)
    id_venta = models.IntegerField()
    serie = models.CharField(max_length=10, db_collation='Modern_Spanish_CI_AS')
    numero = models.IntegerField()
    nit_receptor = models.CharField(max_length=15, db_collation='Modern_Spanish_CI_AS')
    nombre_receptor = models.CharField(max_length=160, db_collation='Modern_Spanish_CI_AS')
    direccion_receptor = models.CharField(max_length=200, db_collation='Modern_Spanish_CI_AS')
    id_usuario_emite = models.IntegerField()
    total = models.DecimalField(max_digits=12, decimal_places=2)
    monto_iva = models.GeneratedField(
        expression=Round(F("total") - F("total") / Value(Decimal("1.12")), 2),
        output_field=_MONEDA,
        db_persist=False,
    )
    estado = models.CharField(max_length=10, db_collation='Modern_Spanish_CI_AS')
    fecha_emision = models.DateTimeField()
    fecha_anulacion = models.DateTimeField(blank=True, null=True)
    motivo_anulacion = models.CharField(max_length=255, db_collation='Modern_Spanish_CI_AS', blank=True, null=True)

    class Meta:
        managed = False
        db_table = "[facturacion].[factura]"


class FacturaDetalle(models.Model):
    id_factura_detalle = models.AutoField(primary_key=True)
    id_factura = models.IntegerField()
    linea = models.SmallIntegerField()
    descripcion = models.CharField(max_length=200, db_collation='Modern_Spanish_CI_AS')
    cantidad = models.IntegerField()
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    descuento = models.DecimalField(max_digits=12, decimal_places=2)
    total = models.GeneratedField(
        expression=F("cantidad") * F("precio_unitario") - F("descuento"),
        output_field=_MONEDA,
        db_persist=False,
    )

    class Meta:
        managed = False
        db_table = "[facturacion].[factura_detalle]"
