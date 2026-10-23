from django import forms

from presentacion.servicios import citas, clientes, examenes


class ExamenVisualForm(forms.Form):
    # Las opciones se cargan en __init__ desde la API.
    cliente = forms.TypedChoiceField(label="Paciente", coerce=int)
    cita = forms.TypedChoiceField(
        label="Cita relacionada", coerce=int, required=False, empty_value=None,
    )
    optometrista = forms.TypedChoiceField(label="Optometrista", coerce=int)

    fecha_examen = forms.DateTimeField(
        label="Fecha y hora del examen",
        input_formats=["%Y-%m-%dT%H:%M"],
        widget=forms.DateTimeInput(
            format="%Y-%m-%dT%H:%M",
            attrs={"type": "datetime-local"}
        )
    )

    motivo_consulta = forms.CharField(
        label="Motivo de consulta",
        max_length=255,
        required=False
    )

    antecedentes = forms.CharField(
        label="Antecedentes",
        required=False,
        widget=forms.Textarea(attrs={"rows": 3})
    )

    agudeza_visual_od = forms.CharField(
        label="Agudeza visual OD (ojo derecho)",
        max_length=10,
        required=False
    )

    agudeza_visual_oi = forms.CharField(
        label="Agudeza visual OI (ojo izquierdo)",
        max_length=10,
        required=False
    )

    presion_intraocular_od = forms.DecimalField(
        label="Presión ocular OD",
        max_digits=4,
        decimal_places=1,
        required=False,
        min_value=0
    )

    presion_intraocular_oi = forms.DecimalField(
        label="Presión ocular OI",
        max_digits=4,
        decimal_places=1,
        required=False,
        min_value=0
    )

    diagnostico = forms.CharField(
        label="Diagnóstico",
        required=False,
        widget=forms.Textarea(attrs={"rows": 3})
    )

    observaciones = forms.CharField(
        label="Observaciones",
        required=False,
        widget=forms.Textarea(attrs={"rows": 3})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["cliente"].choices = [("", "Selecciona un paciente")] + [
            (c.id_cliente, f"{c.nombres} {c.apellidos}") for c in clientes.pacientes_activos()
        ]
        self.fields["cita"].choices = [("", "Sin cita relacionada")] + [
            (c.id_cita, f"Cita #{c.id_cita} - {c.cliente_nombre} - {c.fecha_hora_inicio:%d/%m/%Y %H:%M}")
            for c in citas.citas_para_examen()
        ]
        self.fields["optometrista"].choices = [("", "Selecciona")] + [
            (u.id_usuario, f"{u.nombres} {u.apellidos}") for u in examenes.optometristas_activos()
        ]
