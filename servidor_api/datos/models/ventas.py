"""Modelos del esquema [ventas]."""
from django.db import models
from django.db.models import F

# Columnas calculadas por SQL Server: Django nunca las escribe.
_MONEDA = models.DecimalField(max_digits=12, decimal_places=2)


class DetalleVenta(models.Model):
    id_detalle = models.AutoField(primary_key=True)
    id_venta = models.IntegerField()
    id_producto = models.IntegerField()
    producto_codigo = models.CharField(max_length=30, db_collation='Modern_Spanish_CI_AS')
    producto_nombre = models.CharField(max_length=120, db_collation='Modern_Spanish_CI_AS')
    es_servicio = models.BooleanField()
    cantidad = models.IntegerField()
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    descuento = models.DecimalField(max_digits=12, decimal_places=2)
    subtotal = models.GeneratedField(
        expression=F("cantidad") * F("precio_unitario") - F("descuento"),
        output_field=_MONEDA,
        db_persist=False,
    )

    class Meta:
        managed = False
        db_table = "[ventas].[detalle_venta]"


class MetodoPago(models.Model):
    id_metodo_pago = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=40, db_collation='Modern_Spanish_CI_AS')
    activo = models.BooleanField()

    class Meta:
        managed = False
        db_table = "[ventas].[metodo_pago]"


class OutboxEvento(models.Model):
    id_evento = models.BigAutoField(primary_key=True)
    tipo_evento = models.CharField(max_length=60, db_collation='Modern_Spanish_CI_AS')
    id_agregado = models.CharField(max_length=50, db_collation='Modern_Spanish_CI_AS')
    payload = models.TextField(db_collation='Modern_Spanish_CI_AS')
    fecha_creacion = models.DateTimeField()
    fecha_publicacion = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "[ventas].[outbox_evento]"


class Pago(models.Model):
    id_pago = models.AutoField(primary_key=True)
    id_venta = models.IntegerField()
    id_metodo_pago = models.IntegerField()
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    referencia = models.CharField(max_length=60, db_collation='Modern_Spanish_CI_AS', blank=True, null=True)
    id_usuario = models.IntegerField()
    fecha_pago = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "[ventas].[pago]"


class Venta(models.Model):
    id_venta = models.AutoField(primary_key=True)
    id_cliente = models.IntegerField()
    cliente_nombre = models.CharField(max_length=160, db_collation='Modern_Spanish_CI_AS')
    cliente_nit = models.CharField(max_length=15, db_collation='Modern_Spanish_CI_AS')
    cliente_direccion = models.CharField(max_length=200, db_collation='Modern_Spanish_CI_AS', blank=True, null=True)
    id_vendedor = models.IntegerField()
    vendedor_nombre = models.CharField(max_length=160, db_collation='Modern_Spanish_CI_AS')
    id_receta = models.IntegerField(blank=True, null=True)
    fecha_venta = models.DateTimeField()
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    descuento = models.DecimalField(max_digits=12, decimal_places=2)
    # subtotal lo mantiene el trigger trg_detalle_venta_aiud.
    total = models.GeneratedField(
        expression=F("subtotal") - F("descuento"),
        output_field=_MONEDA,
        db_persist=False,
    )
    estado = models.CharField(max_length=12, db_collation='Modern_Spanish_CI_AS')
    fecha_entrega_estimada = models.DateField(blank=True, null=True)
    observaciones = models.CharField(max_length=255, db_collation='Modern_Spanish_CI_AS', blank=True, null=True)

    class Meta:
        managed = False
        db_table = "[ventas].[venta]"
