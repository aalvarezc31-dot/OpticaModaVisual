"""Modelos del esquema [citas]."""
from django.db import models


class Cita(models.Model):
    id_cita = models.AutoField(primary_key=True)
    id_tipo_cita = models.IntegerField()
    id_cliente = models.IntegerField()
    cliente_nombre = models.CharField(max_length=160, db_collation='Modern_Spanish_CI_AS')
    cliente_telefono = models.CharField(max_length=20, db_collation='Modern_Spanish_CI_AS', blank=True, null=True)
    id_usuario_atiende = models.IntegerField(blank=True, null=True)
    usuario_atiende_nombre = models.CharField(max_length=160, db_collation='Modern_Spanish_CI_AS', blank=True, null=True)
    fecha_hora_inicio = models.DateTimeField()
    fecha_hora_fin = models.DateTimeField()
    estado = models.CharField(max_length=15, db_collation='Modern_Spanish_CI_AS')
    motivo = models.CharField(max_length=255, db_collation='Modern_Spanish_CI_AS', blank=True, null=True)
    motivo_cancelacion = models.CharField(max_length=255, db_collation='Modern_Spanish_CI_AS', blank=True, null=True)
    id_usuario_registra = models.IntegerField()
    fecha_registro = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "[citas].[cita]"


class HorarioAtencion(models.Model):
    id_horario = models.AutoField(primary_key=True)
    id_usuario = models.IntegerField()
    dia_semana = models.SmallIntegerField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()

    class Meta:
        managed = False
        db_table = "[citas].[horario_atencion]"


class TipoCita(models.Model):
    id_tipo_cita = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=60, db_collation='Modern_Spanish_CI_AS')
    duracion_minutos = models.SmallIntegerField()
    requiere_optometrista = models.BooleanField()
    activo = models.BooleanField()

    class Meta:
        managed = False
        db_table = "[citas].[tipo_cita]"
