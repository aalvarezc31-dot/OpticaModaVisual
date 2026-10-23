"""Modelos del esquema [clientes]."""
from django.db import models


class Cliente(models.Model):
    id_cliente = models.AutoField(primary_key=True)
    dpi = models.CharField(max_length=13, db_collation='Modern_Spanish_CI_AS', blank=True, null=True)
    nit = models.CharField(max_length=15, db_collation='Modern_Spanish_CI_AS')
    nombres = models.CharField(max_length=80, db_collation='Modern_Spanish_CI_AS')
    apellidos = models.CharField(max_length=80, db_collation='Modern_Spanish_CI_AS')
    fecha_nacimiento = models.DateField(blank=True, null=True)
    genero = models.CharField(max_length=1, db_collation='Modern_Spanish_CI_AS', blank=True, null=True)
    telefono = models.CharField(max_length=20, db_collation='Modern_Spanish_CI_AS', blank=True, null=True)
    email = models.CharField(max_length=120, db_collation='Modern_Spanish_CI_AS', blank=True, null=True)
    direccion = models.CharField(max_length=200, db_collation='Modern_Spanish_CI_AS', blank=True, null=True)
    activo = models.BooleanField()
    fecha_registro = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "[clientes].[cliente]"
