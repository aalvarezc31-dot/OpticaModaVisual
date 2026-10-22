"""Modelos del esquema [seguridad]."""
from django.db import models


class Bitacora(models.Model):
    id_bitacora = models.BigAutoField(primary_key=True)
    id_usuario = models.IntegerField(blank=True, null=True)
    servicio_origen = models.CharField(max_length=30, db_collation='Modern_Spanish_CI_AS')
    accion = models.CharField(max_length=50, db_collation='Modern_Spanish_CI_AS')
    entidad = models.CharField(max_length=50, db_collation='Modern_Spanish_CI_AS', blank=True, null=True)
    id_entidad = models.CharField(max_length=50, db_collation='Modern_Spanish_CI_AS', blank=True, null=True)
    detalle = models.TextField(db_collation='Modern_Spanish_CI_AS', blank=True, null=True)
    ip = models.CharField(max_length=45, db_collation='Modern_Spanish_CI_AS', blank=True, null=True)
    fecha = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "[seguridad].[bitacora]"


class RefreshToken(models.Model):
    id_token = models.BigAutoField(primary_key=True)
    id_usuario = models.IntegerField()
    token_hash = models.CharField(max_length=255, db_collation='Modern_Spanish_CI_AS')
    fecha_emision = models.DateTimeField()
    fecha_expira = models.DateTimeField()
    revocado = models.BooleanField()

    class Meta:
        managed = False
        db_table = "[seguridad].[refresh_token]"


class Rol(models.Model):
    id_rol = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=30, db_collation='Modern_Spanish_CI_AS')
    descripcion = models.CharField(max_length=150, db_collation='Modern_Spanish_CI_AS', blank=True, null=True)

    class Meta:
        managed = False
        db_table = "[seguridad].[rol]"
        verbose_name = "rol"
        verbose_name_plural = "roles"

    def __str__(self):
        return self.nombre


class Usuario(models.Model):
    id_usuario = models.AutoField(primary_key=True)
    id_rol = models.IntegerField(verbose_name="rol")
    nombres = models.CharField(max_length=80, db_collation='Modern_Spanish_CI_AS')
    apellidos = models.CharField(max_length=80, db_collation='Modern_Spanish_CI_AS')
    username = models.CharField(max_length=40, db_collation='Modern_Spanish_CI_AS')
    email = models.CharField(max_length=120, db_collation='Modern_Spanish_CI_AS')
    password_hash = models.CharField(max_length=255, db_collation='Modern_Spanish_CI_AS')
    telefono = models.CharField(max_length=20, db_collation='Modern_Spanish_CI_AS', blank=True, null=True)
    activo = models.BooleanField()
    ultimo_acceso = models.DateTimeField(blank=True, null=True)
    fecha_creacion = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "[seguridad].[usuario]"
        verbose_name = "usuario del sistema"
        verbose_name_plural = "usuarios del sistema (con rol)"

    def __str__(self):
        return f"{self.username} ({self.nombres} {self.apellidos})"
