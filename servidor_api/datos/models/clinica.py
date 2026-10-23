"""Modelos del esquema [clinica]."""
from django.db import models


class ExamenVisual(models.Model):
    id_examen = models.AutoField(primary_key=True)
    id_cliente = models.IntegerField()
    id_cita = models.IntegerField(blank=True, null=True)
    id_optometrista = models.IntegerField()
    optometrista_nombre = models.CharField(max_length=160, db_collation='Modern_Spanish_CI_AS')
    fecha_examen = models.DateTimeField()
    motivo_consulta = models.CharField(max_length=255, db_collation='Modern_Spanish_CI_AS', blank=True, null=True)
    antecedentes = models.TextField(db_collation='Modern_Spanish_CI_AS', blank=True, null=True)
    agudeza_visual_od = models.CharField(max_length=10, db_collation='Modern_Spanish_CI_AS', blank=True, null=True)
    agudeza_visual_oi = models.CharField(max_length=10, db_collation='Modern_Spanish_CI_AS', blank=True, null=True)
    presion_intraocular_od = models.DecimalField(max_digits=4, decimal_places=1, blank=True, null=True)
    presion_intraocular_oi = models.DecimalField(max_digits=4, decimal_places=1, blank=True, null=True)
    diagnostico = models.TextField(db_collation='Modern_Spanish_CI_AS', blank=True, null=True)
    observaciones = models.TextField(db_collation='Modern_Spanish_CI_AS', blank=True, null=True)

    class Meta:
        managed = False
        db_table = "[clinica].[examen_visual]"


class RecetaOptica(models.Model):
    id_receta = models.AutoField(primary_key=True)
    id_examen = models.IntegerField()
    od_esfera = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    od_cilindro = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    od_eje = models.SmallIntegerField(blank=True, null=True)
    od_adicion = models.DecimalField(max_digits=4, decimal_places=2, blank=True, null=True)
    oi_esfera = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    oi_cilindro = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    oi_eje = models.SmallIntegerField(blank=True, null=True)
    oi_adicion = models.DecimalField(max_digits=4, decimal_places=2, blank=True, null=True)
    distancia_pupilar = models.DecimalField(max_digits=4, decimal_places=1, blank=True, null=True)
    tipo_lente = models.CharField(max_length=50, db_collation='Modern_Spanish_CI_AS', blank=True, null=True)
    tratamiento = models.CharField(max_length=100, db_collation='Modern_Spanish_CI_AS', blank=True, null=True)
    indicaciones = models.TextField(db_collation='Modern_Spanish_CI_AS', blank=True, null=True)
    fecha_emision = models.DateField()
    fecha_vencimiento = models.DateField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "[clinica].[receta_optica]"
