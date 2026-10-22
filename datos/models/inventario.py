"""Modelos del esquema [inventario]."""
from django.db import models


class CategoriaProducto(models.Model):
    id_categoria = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=50, db_collation='Modern_Spanish_CI_AS')
    descripcion = models.CharField(max_length=150, db_collation='Modern_Spanish_CI_AS', blank=True, null=True)

    class Meta:
        managed = False
        db_table = "[inventario].[categoria_producto]"


class Marca(models.Model):
    id_marca = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=60, db_collation='Modern_Spanish_CI_AS')

    class Meta:
        managed = False
        db_table = "[inventario].[marca]"


class MovimientoInventario(models.Model):
    id_movimiento = models.BigAutoField(primary_key=True)
    id_producto = models.IntegerField()
    id_proveedor = models.IntegerField(blank=True, null=True)
    id_usuario = models.IntegerField()
    id_venta = models.IntegerField(blank=True, null=True)
    tipo = models.CharField(max_length=10, db_collation='Modern_Spanish_CI_AS')
    cantidad = models.IntegerField()
    costo_unitario = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    motivo = models.CharField(max_length=255, db_collation='Modern_Spanish_CI_AS', blank=True, null=True)
    fecha = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "[inventario].[movimiento_inventario]"


class Producto(models.Model):
    id_producto = models.AutoField(primary_key=True)
    codigo = models.CharField(max_length=30, db_collation='Modern_Spanish_CI_AS')
    id_categoria = models.IntegerField()
    id_marca = models.IntegerField(blank=True, null=True)
    id_proveedor = models.IntegerField(blank=True, null=True)
    nombre = models.CharField(max_length=120, db_collation='Modern_Spanish_CI_AS')
    modelo = models.CharField(max_length=60, db_collation='Modern_Spanish_CI_AS', blank=True, null=True)
    color = models.CharField(max_length=40, db_collation='Modern_Spanish_CI_AS', blank=True, null=True)
    material = models.CharField(max_length=60, db_collation='Modern_Spanish_CI_AS', blank=True, null=True)
    descripcion = models.CharField(max_length=255, db_collation='Modern_Spanish_CI_AS', blank=True, null=True)
    es_servicio = models.BooleanField()
    precio_costo = models.DecimalField(max_digits=12, decimal_places=2)
    precio_venta = models.DecimalField(max_digits=12, decimal_places=2)
    stock_actual = models.IntegerField()
    stock_minimo = models.IntegerField()
    activo = models.BooleanField()
    fecha_creacion = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "[inventario].[producto]"


class Proveedor(models.Model):
    id_proveedor = models.AutoField(primary_key=True)
    nit = models.CharField(max_length=15, db_collation='Modern_Spanish_CI_AS')
    nombre = models.CharField(max_length=120, db_collation='Modern_Spanish_CI_AS')
    contacto = models.CharField(max_length=100, db_collation='Modern_Spanish_CI_AS', blank=True, null=True)
    telefono = models.CharField(max_length=20, db_collation='Modern_Spanish_CI_AS', blank=True, null=True)
    email = models.CharField(max_length=120, db_collation='Modern_Spanish_CI_AS', blank=True, null=True)
    direccion = models.CharField(max_length=200, db_collation='Modern_Spanish_CI_AS', blank=True, null=True)
    activo = models.BooleanField()

    class Meta:
        managed = False
        db_table = "[inventario].[proveedor]"
